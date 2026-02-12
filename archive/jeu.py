"""
Jeu de plateforme contrôlé par micro:bit (ou clavier).
POC pédagogique — Python + Pygame + Serial.
"""

# ──────────────────────────────────────────────
# 1. Imports
# ──────────────────────────────────────────────
import sys
import glob
import threading

import pygame
import serial

# ──────────────────────────────────────────────
# 2. Constantes
# ──────────────────────────────────────────────

# Écran
LARGEUR = 800
HAUTEUR = 600
FPS = 60

# Couleurs (R, G, B)
BLANC = (255, 255, 255)
NOIR = (0, 0, 0)
BLEU = (50, 120, 220)
VERT = (34, 180, 80)
GRIS = (180, 180, 180)
ROUGE = (220, 60, 60)

# Physique du joueur
VITESSE_DEPLACEMENT = 5
VITESSE_SERIAL = 2
FORCE_SAUT = -12
GRAVITE = 0.6
VITESSE_MAX_CHUTE = 10

# Taille du joueur
JOUEUR_LARGEUR = 30
JOUEUR_HAUTEUR = 40

# Serial
BAUD_RATE = 115200


# ──────────────────────────────────────────────
# 3. Auto-détection du port micro:bit
# ──────────────────────────────────────────────

def detecter_port_microbit():
    """Cherche un port série correspondant à un micro:bit branché."""
    # Motifs courants selon l'OS
    motifs = [
        "/dev/tty.usbmodem*",   # macOS
        "/dev/ttyACM*",         # Linux
        "COM*",                 # Windows
    ]
    for motif in motifs:
        ports = glob.glob(motif)
        if ports:
            return ports[0]
    return None


# ──────────────────────────────────────────────
# 4. Classe Joueur
# ──────────────────────────────────────────────

class Joueur:
    """Le personnage contrôlable (rectangle coloré)."""

    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, JOUEUR_LARGEUR, JOUEUR_HAUTEUR)
        self.vitesse_x = 0
        self.vitesse_y = 0
        self.au_sol = False

    def appliquer_gravite(self):
        """Applique la gravité à la vitesse verticale."""
        self.vitesse_y += GRAVITE
        if self.vitesse_y > VITESSE_MAX_CHUTE:
            self.vitesse_y = VITESSE_MAX_CHUTE

    def sauter(self):
        """Fait sauter le joueur s'il est au sol."""
        if self.au_sol:
            self.vitesse_y = FORCE_SAUT
            self.au_sol = False

    def mettre_a_jour(self, plateformes):
        """Met à jour la position et gère les collisions."""
        # Déplacement horizontal
        self.rect.x += self.vitesse_x

        # Empêcher de sortir de l'écran à gauche/droite
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > LARGEUR:
            self.rect.right = LARGEUR

        # Déplacement vertical (gravité)
        self.appliquer_gravite()
        self.rect.y += self.vitesse_y

        # Collision avec les plateformes et le sol
        self.au_sol = False
        for plateforme in plateformes:
            if self.rect.colliderect(plateforme.rect) and self.vitesse_y >= 0:
                # On ne corrige que si le joueur tombe (pas en montant)
                if self.rect.bottom > plateforme.rect.top and self.rect.top < plateforme.rect.top:
                    self.rect.bottom = plateforme.rect.top
                    self.vitesse_y = 0
                    self.au_sol = True

        # Sol (bas de l'écran)
        if self.rect.bottom >= HAUTEUR:
            self.rect.bottom = HAUTEUR
            self.vitesse_y = 0
            self.au_sol = True

    def dessiner(self, ecran):
        """Dessine le joueur à l'écran."""
        pygame.draw.rect(ecran, BLEU, self.rect)
        # Petits yeux pour donner du caractère
        oeil_g = pygame.Rect(self.rect.x + 7, self.rect.y + 8, 5, 5)
        oeil_d = pygame.Rect(self.rect.x + 18, self.rect.y + 8, 5, 5)
        pygame.draw.rect(ecran, BLANC, oeil_g)
        pygame.draw.rect(ecran, BLANC, oeil_d)


# ──────────────────────────────────────────────
# 5. Classe Plateforme
# ──────────────────────────────────────────────

class Plateforme:
    """Une plateforme sur laquelle le joueur peut se poser."""

    def __init__(self, x, y, largeur, hauteur, couleur=VERT):
        self.rect = pygame.Rect(x, y, largeur, hauteur)
        self.couleur = couleur

    def dessiner(self, ecran):
        """Dessine la plateforme à l'écran."""
        pygame.draw.rect(ecran, self.couleur, self.rect)


# ──────────────────────────────────────────────
# 6. Lecture serial (thread séparé)
# ──────────────────────────────────────────────

# Variable partagée entre le thread serial et la boucle de jeu
derniere_commande = "tranquille"
verrou_commande = threading.Lock()


def lire_serial(port):
    """Lit en continu les lignes envoyées par le micro:bit."""
    global derniere_commande
    try:
        connexion = serial.Serial(port, BAUD_RATE, timeout=1)
        print(f"[serial] Connecté sur {port}")
        while True:
            ligne = connexion.readline().decode("utf-8", errors="ignore").strip()
            if ligne:
                with verrou_commande:
                    derniere_commande = ligne.lower()
    except serial.SerialException as e:
        print(f"[serial] Erreur : {e}")
    except Exception as e:
        print(f"[serial] Erreur inattendue : {e}")


def demarrer_thread_serial():
    """Détecte le port et lance le thread de lecture serial."""
    port = detecter_port_microbit()
    if port:
        print(f"[serial] micro:bit détecté sur {port}")
        thread = threading.Thread(target=lire_serial, args=(port,), daemon=True)
        thread.start()
        return True
    else:
        print("[serial] Aucun micro:bit détecté — mode clavier uniquement")
        return False


# ──────────────────────────────────────────────
# 7. Boucle de jeu principale
# ──────────────────────────────────────────────

def creer_plateformes():
    """Crée le parcours de plateformes."""
    return [
        # Sol principal (toute la largeur)
        Plateforme(0, HAUTEUR - 20, LARGEUR, 20, GRIS),
        # Plateformes du parcours (de gauche à droite, de bas en haut)
        Plateforme(50, 480, 150, 15),
        Plateforme(280, 400, 150, 15),
        Plateforme(500, 330, 150, 15),
        Plateforme(300, 240, 150, 15),
        Plateforme(80, 160, 150, 15),
        # Plateforme finale en haut
        Plateforme(550, 120, 200, 15, ROUGE),
    ]


def main():
    """Point d'entrée du jeu."""
    global derniere_commande

    # Initialisation de Pygame
    pygame.init()
    ecran = pygame.display.set_mode((LARGEUR, HAUTEUR))
    pygame.display.set_caption("Jeu de plateforme — micro:bit")
    horloge = pygame.time.Clock()

    # Création des objets de jeu
    joueur = Joueur(100, HAUTEUR - 60)
    plateformes = creer_plateformes()

    # Lancer la lecture serial (si micro:bit branché)
    microbit_connecte = demarrer_thread_serial()

    # Police pour l'affichage d'infos
    police = pygame.font.SysFont(None, 24)

    en_cours = True
    while en_cours:
        # ── Gestion des événements ──
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                en_cours = False
            # Saut au clavier (sur appui, pas en continu)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    joueur.sauter()
                if event.key == pygame.K_ESCAPE:
                    en_cours = False

        # ── Entrées clavier (maintien) ──
        touches = pygame.key.get_pressed()
        mouvement_clavier = 0
        if touches[pygame.K_LEFT]:
            mouvement_clavier -= VITESSE_DEPLACEMENT
        if touches[pygame.K_RIGHT]:
            mouvement_clavier += VITESSE_DEPLACEMENT

        # ── Entrées serial ──
        mouvement_serial = 0
        with verrou_commande:
            commande = derniere_commande

        if commande == "avancer":
            mouvement_serial = VITESSE_SERIAL
        elif commande == "reculer":
            mouvement_serial = -VITESSE_SERIAL
        elif commande == "sauter":
            joueur.sauter()
        # "tranquille" → pas de mouvement serial

        # Les deux inputs se combinent
        joueur.vitesse_x = mouvement_clavier + mouvement_serial

        # ── Mise à jour ──
        joueur.mettre_a_jour(plateformes)

        # ── Affichage ──
        ecran.fill(NOIR)

        # Dessiner les plateformes
        for plateforme in plateformes:
            plateforme.dessiner(ecran)

        # Dessiner le joueur
        joueur.dessiner(ecran)

        # Indication du mode de contrôle
        if microbit_connecte:
            texte = police.render("micro:bit + clavier", True, BLANC)
        else:
            texte = police.render("clavier uniquement (pas de micro:bit)", True, BLANC)
        ecran.blit(texte, (10, 10))

        # Indication des contrôles
        texte_controles = police.render(
            "Flèches: bouger | Espace: sauter | Échap: quitter", True, GRIS
        )
        ecran.blit(texte_controles, (10, 35))

        # Affichage de la dernière commande serial reçue
        couleur_cmd = BLANC if commande == "tranquille" else (255, 220, 50)
        texte_cmd = police.render(f"Commande serial : {commande}", True, couleur_cmd)
        ecran.blit(texte_cmd, (10, 60))

        pygame.display.flip()
        horloge.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
