"""Coups speciaux Street Fighter II Turbo.

Chaque macro = {1: etapes_P1, 2: etapes_P2}.
P1 est a gauche de l'ecran, P2 a droite (directions inversees).

Format des etapes :
  ["key1", "key2"]          → maintenu MACRO_DELAY secondes
  (["key1", "key2"], 0.9)   → maintenu 0.9 secondes (pour les charges)

Les eleves peuvent ajouter de nouvelles macros en entrainant un geste ML
sur leur micro:bit et en ajoutant l'entree ici.
"""

MACRO_DELAY = 0.06   # duree par defaut d'une etape
CHARGE_TIME = 0.9    # duree de charge (moves charges)
MASH_DELAY = 0.03    # delai entre appuis (mashing)

# ── Touches par joueur ───────────────────────────────────────────────
# P1 (a gauche) : "right" = avancer, "left" = reculer
# P2 (a droite) : "h" = avancer (gauche ecran), "k" = reculer (droite ecran)

FWD   = {1: "right", 2: "h"}
BACK  = {1: "left",  2: "k"}
DOWN  = {1: "down",  2: "j"}
UP    = {1: "up",    2: "u"}

PUNCH = {1: "s", 2: "o"}   # poing (coup special)
KICK  = {1: "x", 2: "l"}   # pied


# ── Motions de base ──────────────────────────────────────────────────

def _both(fn):
    """Genere les etapes pour les deux joueurs."""
    return {1: fn(1), 2: fn(2)}


def _qcf(p, btn):
    """Quarter circle forward : ↓ ↘ → + btn"""
    return [[DOWN[p]], [DOWN[p], FWD[p]], [FWD[p], btn[p]]]


def _qcb(p, btn):
    """Quarter circle back : ↓ ↙ ← + btn"""
    return [[DOWN[p]], [DOWN[p], BACK[p]], [BACK[p], btn[p]]]


def _dp(p, btn):
    """Dragon punch : → ↓ ↘ + btn"""
    return [[FWD[p]], [DOWN[p]], [DOWN[p], FWD[p], btn[p]]]


def _hcf(p, btn):
    """Half circle forward : ← ↙ ↓ ↘ → + btn"""
    return [
        [BACK[p]], [BACK[p], DOWN[p]], [DOWN[p]],
        [DOWN[p], FWD[p]], [FWD[p], btn[p]],
    ]


def _charge_fb(p, btn):
    """Charge ← → + btn"""
    return [([BACK[p]], CHARGE_TIME), [FWD[p], btn[p]]]


def _charge_du(p, btn):
    """Charge ↓ ↑ + btn"""
    return [([DOWN[p]], CHARGE_TIME), [UP[p], btn[p]]]


def _360(p, btn):
    """360° + btn"""
    return [
        [FWD[p]], [FWD[p], UP[p]], [UP[p]], [UP[p], BACK[p]],
        [BACK[p]], [BACK[p], DOWN[p]], [DOWN[p]], [DOWN[p], FWD[p], btn[p]],
    ]


def _tiger_knee(p, btn):
    """↓ ↘ → ↗ + btn"""
    return [[DOWN[p]], [DOWN[p], FWD[p]], [FWD[p]], [FWD[p], UP[p], btn[p]]]


def _mash(p, btn, n=5):
    """Appuis rapides (mashing)."""
    steps = []
    for _ in range(n):
        steps.append(([btn[p]], MASH_DELAY))
        steps.append(([], MASH_DELAY))
    return steps


# ── Coups speciaux par personnage ────────────────────────────────────

MACROS = {
    # ── Ryu / Ken ──
    "hadouken":     _both(lambda p: _qcf(p, PUNCH)),
    "shoryuken":    _both(lambda p: _dp(p, PUNCH)),
    "tatsumaki":    _both(lambda p: _qcb(p, KICK)),

    # ── Guile ──
    "sonic_boom":   _both(lambda p: _charge_fb(p, PUNCH)),
    "flash_kick":   _both(lambda p: _charge_du(p, KICK)),

    # ── E. Honda ──
    "hundred_hand": _both(lambda p: _mash(p, PUNCH)),
    "sumo_headbutt": _both(lambda p: _charge_fb(p, PUNCH)),
    "sumo_smash":   _both(lambda p: _charge_du(p, KICK)),

    # ── Blanka ──
    "electricity":  _both(lambda p: _mash(p, PUNCH)),
    "rolling_h":    _both(lambda p: _charge_fb(p, PUNCH)),
    "rolling_v":    _both(lambda p: _charge_du(p, KICK)),

    # ── Dhalsim ──
    "yoga_fire":    _both(lambda p: _qcf(p, PUNCH)),
    "yoga_flame":   _both(lambda p: _hcf(p, PUNCH)),
    "yoga_teleport": _both(lambda p: _dp(p, PUNCH)),

    # ── Zangief ──
    "lariat":       _both(lambda p: _mash(p, PUNCH, 3)),
    "pile_driver":  _both(lambda p: _360(p, PUNCH)),

    # ── Balrog (Boxer) ──
    "turn_punch":   _both(lambda p: [([PUNCH[p]], 2.0)]),
    "dash_punch":   _both(lambda p: _charge_fb(p, PUNCH)),

    # ── Vega (Claw) ──
    "claw_dive":    _both(lambda p: _charge_du(p, KICK)),
    "wall_leap":    _both(lambda p: _charge_fb(p, KICK)),
    "claw_roll":    _both(lambda p: _charge_fb(p, PUNCH)),

    # ── Sagat ──
    "tiger_shot":     _both(lambda p: _qcf(p, PUNCH)),
    "tiger_uppercut": _both(lambda p: _dp(p, PUNCH)),
    "tiger_knee":     _both(lambda p: _tiger_knee(p, KICK)),

    # ── Chun-Li ──
    "lightning_kick":  _both(lambda p: _mash(p, KICK)),
    "spinning_bird":   _both(lambda p: _charge_du(p, KICK)),
    "kikoken":         _both(lambda p: _charge_fb(p, PUNCH)),

    # ── M. Bison ──
    "psycho_crusher": _both(lambda p: _charge_fb(p, PUNCH)),
    "scissor_kick":   _both(lambda p: _charge_fb(p, KICK)),
    "head_stomp":     _both(lambda p: _charge_du(p, KICK)),
}
