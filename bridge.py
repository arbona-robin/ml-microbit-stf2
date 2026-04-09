#!/usr/bin/env python3
"""Bridge micro:bit → clavier : lit le port série et simule des touches.

La lecture série tourne dans un thread dédié pour ne jamais être bloquée
par les time.sleep() de la simulation clavier (pynput).

Les micro:bit émetteurs envoient directement les touches clavier à simuler.
Le récepteur transmet "P1:touche" ou "P2:touche" via USB série.
Combos avec "+" : "up+z" appuie simultanément sur les deux touches.
Mots-clés : définis dans MACROS (ex: "hadouken" → séquence de touches).
"""

import queue
import sys
import termios
import threading
import time
from difflib import SequenceMatcher
import serial
import serial.tools.list_ports
from pynput.keyboard import Key, Controller
from macros import MACROS, MACRO_DELAY

# ── Configuration ────────────────────────────────────────────────────

HOLD_MODE = True  # True = maintien des touches, False = tap uniquement

# Touches spéciales (nom → touche pynput). Un caractère seul est envoyé tel quel.
SPECIAL_KEYS = {
    "up": Key.up, "down": Key.down, "left": Key.left, "right": Key.right,
    "space": Key.space, "enter": Key.enter,
}

# Touches toujours en tap (press+release), jamais maintenues même en HOLD_MODE
TAP_KEYS = {"z", "x", "l", "m"}

TAP_DURATION = 0.05

# Traduction code radio → action (nouveau protocole 1 caractère)
PLAYER_CODES = {
    1: {
        "0": "none", "1": "left", "2": "right", "3": "up", "4": "down",
        "z": "z", "x": "x", "!": "hadouken",
    },
    2: {
        "0": "none", "1": "h", "2": "k", "3": "u", "4": "j",
        "m": "m", "l": "l", "!": "hadouken",
    },
}

# Ensemble de toutes les actions valides (pour rétro-compat et fuzzy matching)
_ALL_ACTIONS = (
    set(SPECIAL_KEYS) | TAP_KEYS | {"none"} | set(MACROS)
    | {"h", "k", "u", "j", "m", "l"}
)

# ── Couleurs ANSI ────────────────────────────────────────────────────
R = "\033[0m"
DIM = "\033[2m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"

PLAYER_COLORS = {1: BLUE, 2: MAGENTA}

# ── Logique ──────────────────────────────────────────────────────────

keyboard = Controller()
player_seen = set()
held_keys = {1: set(), 2: set()}
cmd_queue = queue.Queue()


def find_microbit():
    """Cherche le port série du micro:bit (par VID USB, ignore les ports fantômes)."""
    for port in serial.tools.list_ports.comports():
        if port.vid == 0x0D28:  # ARM/micro:bit vendor ID
            return port.device
    return None


def resolve_key(name):
    """Convertit un nom de touche en objet pynput."""
    name = name.strip()
    if name in SPECIAL_KEYS:
        return SPECIAL_KEYS[name]
    if len(name) == 1:
        return name
    return None


def fuzzy_match(text, candidates, threshold=0.6):
    """Meilleur candidat par similarité (SequenceMatcher). None si sous le seuil."""
    best, best_ratio = None, 0
    for c in candidates:
        r = SequenceMatcher(None, text, c).ratio()
        if r > best_ratio:
            best, best_ratio = c, r
    return best if best_ratio >= threshold else None


def translate(player, code):
    """Traduit un code radio en action. Rétro-compatible avec l'ancien firmware."""
    # Nouveau protocole (1 caractère)
    action = PLAYER_CODES.get(player, {}).get(code)
    if action:
        return action
    # Ancien protocole (nom complet déjà valide)
    if code in _ALL_ACTIONS:
        return code
    # Fuzzy matching sur les corruptions résiduelles
    match = fuzzy_match(code, _ALL_ACTIONS)
    if match:
        return match
    return code


def release_all(player):
    for k in held_keys[player]:
        keyboard.release(k)
    held_keys[player] = set()


def tap(keys):
    for k in keys:
        keyboard.press(k)
    time.sleep(TAP_DURATION)
    for k in keys:
        keyboard.release(k)


def do_macro(steps):
    """Exécute une macro. Chaque étape = liste de touches ou (touches, duree)."""
    current = set()
    for step in steps:
        if isinstance(step, tuple):
            keys, delay = step
        else:
            keys, delay = step, MACRO_DELAY
        target = {resolve_key(k) for k in keys} - {None}
        for k in current - target:
            keyboard.release(k)
        for k in target - current:
            keyboard.press(k)
        current = target
        time.sleep(delay)
    for k in current:
        keyboard.release(k)


def player_prefix(player):
    if len(player_seen) < 2:
        return ""
    return f"{PLAYER_COLORS[player]}P{player}{R} "


# Labels lisibles pour les codes radio
CODE_LABELS = {
    "0": "0:none", "1": "1:gauche", "2": "2:droite", "3": "3:haut", "4": "4:bas",
    "!": "!:hadouken",
}


def fmt_action(action, raw):
    """Affiche le code brut → action si traduction, sinon juste l'action."""
    label = CODE_LABELS.get(raw)
    if label:
        return label
    if raw != action:
        return f"{raw}→{action}"
    return action


def handle(action, player, raw=""):
    prefix = player_prefix(player)

    # Macro (ex: hadouken)
    if action in MACROS:
        steps = MACROS[action].get(player)
        if steps:
            release_all(player)
            do_macro(steps)
            print(f"  {prefix}{YELLOW}>> {fmt_action(action, raw)}{R}")
        return

    # Relâcher tout
    if action == "none":
        release_all(player)
        print(f"  {prefix}{CYAN}-- {fmt_action(action, raw)}{R}")
        return

    # Résoudre les touches (supporte les combos avec +)
    parts = action.split("+")
    keys = [resolve_key(p) for p in parts]
    keys = [k for k in keys if k is not None]

    if not keys:
        print(f"  {prefix}{RED}?? {fmt_action(action, raw)}{R}")
        return

    is_tap = len(keys) > 1 or any(p.strip() in TAP_KEYS for p in parts) or not HOLD_MODE

    if is_tap:
        release_all(player)
        tap(keys)
        print(f"  {prefix}{GREEN}>> {fmt_action(action, raw)}{R}")
    else:
        if held_keys[player] == set(keys):
            return
        release_all(player)
        keyboard.press(keys[0])
        held_keys[player] = set(keys)
        print(f"  {prefix}{BLUE}>> {fmt_action(action, raw)}{R}")


# ── Thread de lecture série ──────────────────────────────────────────

def serial_reader(ser, stop_event):
    while not stop_event.is_set():
        try:
            raw = ser.readline()
            if not raw:
                continue
            line = raw.decode("utf-8", errors="ignore").strip().lower()
            if not line:
                continue
            if "--debug" in sys.argv:
                print(f"  {DIM}[raw] {line!r}  ({len(raw)}B){R}")
            if line.startswith("p1:"):
                raw = line[3:]
                cmd_queue.put((1, translate(1, raw), raw))
            elif line.startswith("p2:"):
                raw = line[3:]
                cmd_queue.put((2, translate(2, raw), raw))
        except (serial.SerialException, OSError):
            cmd_queue.put(None)
            return


# ── Programme principal ──────────────────────────────────────────────

print("=== Bridge micro:bit → clavier ===")
print(f"Mode : {'maintien' if HOLD_MODE else 'tap'}")
print()


def connect():
    while True:
        port = find_microbit()
        if port is None:
            print("Aucun micro:bit détecté, nouvelle tentative dans 3s…")
            time.sleep(3)
            continue
        try:
            ser = serial.Serial(
                port=port, baudrate=115200,
                bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE, timeout=1,
            )
            print(f"Connecté sur {port}")
            return ser
        except serial.SerialException as e:
            print(f"Erreur : {e}")
            time.sleep(3)


ser = connect()
print("En attente de commandes… (Ctrl+C pour quitter)\n")

# Désactiver l'écho terminal (les touches simulées par pynput ne polluent plus)
_fd = sys.stdin.fileno()
_old_term = termios.tcgetattr(_fd)
_new_term = termios.tcgetattr(_fd)
_new_term[3] = _new_term[3] & ~termios.ECHO
termios.tcsetattr(_fd, termios.TCSADRAIN, _new_term)

stop_event = threading.Event()
reader_thread = threading.Thread(target=serial_reader, args=(ser, stop_event), daemon=True)
reader_thread.start()

try:
    while True:
        try:
            item = cmd_queue.get(timeout=0.5)
        except queue.Empty:
            continue

        if item is None:
            print("Connexion perdue, reconnexion…")
            for p in list(held_keys):
                release_all(p)
            ser.close()
            ser = connect()
            stop_event = threading.Event()
            reader_thread = threading.Thread(
                target=serial_reader, args=(ser, stop_event), daemon=True
            )
            reader_thread.start()
            continue

        player, action, raw = item
        if player not in player_seen:
            player_seen.add(player)
            print(f"  {PLAYER_COLORS[player]}Joueur {player} détecté{R}")
        handle(action, player, raw)

except KeyboardInterrupt:
    print("\nArrêt.")
    stop_event.set()
    for p in list(held_keys):
        release_all(p)
    if ser:
        ser.close()
finally:
    termios.tcsetattr(_fd, termios.TCSADRAIN, _old_term)
