# JDEV2026 — MicroPython sur Pico W
# Auteur : Eric Duvieilbourg — CNRS / LEMAR
# Usage pédagogique JDEV2026 : voir LICENSE_CODE_JDEV2026.md
# =============================================================================
#  config.py — Configuration centrale du projet JDEV2026
#  Modifiez CE fichier uniquement pour adapter le projet à votre environnement.
#
#  Ce projet supporte AUTOMATIQUEMENT deux types de cartes sans rien changer :
#    - Maker Pi Pico  + capteur SHT30 (M5Stack ENV III)   → I2C, GP0/GP1
#    - Pico Bricks Base Kit + capteur DHT11 (< juil. 2024) → 1-fil, GP11
#    - Pico Bricks Base Kit + capteur SHTC3 (≥ juil. 2024) → I2C, GP4/GP5
#  La détection se fait automatiquement au démarrage (voir acquisition.py).
#
#  ═══════════════════════════════════════════════════════════════════════
#  👉 PARTICIPANTS : modifiez UNIQUEMENT la ligne USER_INITIALS ci-dessous
#  ═══════════════════════════════════════════════════════════════════════
# =============================================================================

# ─── Nom du dossier projet sur le Pico ───────────────────────────────────────
# SOURCE UNIQUE pour le nom du dossier — modifiez uniquement ici si vous
# renommez le dossier. main.py et test_sensor.py le lisent automatiquement.
# (main.py en a besoin AVANT de pouvoir importer ce fichier — voir la
#  constante dupliquée en haut de main.py avec le même commentaire.)
PROJECT_DIR = "JDEV2026"

# ─── Identité du participant ─────────────────────────────────────────────────
# Vos initiales en minuscules (2 lettres). Détermine automatiquement le SSID
# WiFi et le nom affiché sur le dashboard — pour identifier facilement votre
# Pico parmi les 20 de l'atelier.
# Exemple : "ed" pour Eric Duvieilbourg → SSID "edPicoW-JDEV"
USER_INITIALS = "ed"

# ─── WiFi — Mode Point d'Accès (AP) ─────────────────────────────────────────
WIFI_SSID     = f"{USER_INITIALS}PicoW-JDEV"
WIFI_PASSWORD = "micropython"
WIFI_CHANNEL  = 6
WIFI_IP       = "192.168.4.1"
WIFI_SUBNET   = "255.255.255.0"
WIFI_GATEWAY  = "192.168.4.1"
WIFI_DNS      = "192.168.4.1"
HTTP_PORT     = 80

# ─── Acquisition capteur — fréquence ─────────────────────────────────────────
# IMPORTANT : le DHT11 (Pico Bricks ancienne version) est limité à 1 mesure
# toutes les 200ms minimum par contrainte matérielle. 1Hz convient aux deux
# familles de capteurs (SHT30/SHTC3 I2C et DHT11) sans aucune modification.
SAMPLE_RATE_HZ = 1

# ─── Détection automatique du capteur ────────────────────────────────────────
# ⚠ CONTRAINTE MATÉRIELLE RP2040/RP2350 (bug confirmé, voir acquisition.py) :
# initialiser le bus I2C0 sur un second jeu de broches après un premier essai
# CASSE DÉFINITIVEMENT le bus jusqu'au prochain reset matériel. On ne peut
# donc tester qu'UN SEUL jeu de broches I2C par run, jamais les deux.
#
# Par défaut (BOARD_I2C_PINS="auto"), le système utilise GP4/GP5
# (Pico Bricks) — ce qui couvre la majorité des capteurs I2C de l'atelier.
#
# Si vous avez un Maker Pi Pico avec SHT30 sur GP0/GP1, changez cette
# valeur à "maker" avant de lancer main.py :
#   BOARD_I2C_PINS = "maker"   # → teste GP0/GP1 au lieu de GP4/GP5
# BOARD_I2C_PINS = "maker"   # "maker" (GP0/GP1) pour Maker Pi Pico + ENV III ;
BOARD_I2C_PINS = "bricks"   # "bricks" = GP4/GP5

# Ordre de test au démarrage (voir acquisition.py → detect_sensor()) :
#   1. SHTC3  (I2C, adresse fixe 0x70)     → Pico Bricks version ≥ juil. 2024
#   2. SHT30  (I2C, adresse 0x44 ou 0x45)  → Maker Pi Pico + M5Stack ENV III
#      (sur le bus choisi par BOARD_I2C_PINS ci-dessus, un seul des deux)
#   3. DHT11  (1-fil, GP11)                → Pico Bricks version < juil. 2024
#      (indépendant du bus I2C, toujours testé en complément, sans risque)
#   4. Aucun capteur trouvé → mode simulation automatique
AUTO_DETECT_SENSOR = True

# Pins I2C pour SHT30 (Maker Pi Pico) et SHTC3 (Pico Bricks I2C)
I2C_ID            = 0
I2C_SDA_PIN_MAKER = 0     # Maker Pi Pico : GP0
I2C_SCL_PIN_MAKER = 1     # Maker Pi Pico : GP1
I2C_SDA_PIN_BRICKS = 4    # Pico Bricks   : GP4
I2C_SCL_PIN_BRICKS = 5    # Pico Bricks   : GP5

SHT30_ADDR  = 0x44        # ou 0x45 selon le lot de capteurs
SHTC3_ADDR  = 0x70        # adresse fixe, non configurable

# Pin DHT11 (Pico Bricks ancienne version, 1-fil)
DHT11_PIN = 11            # GP11 — confirmé sur le matériel réel

# ─── Stockage ─────────────────────────────────────────────────────────────────
SD_SPI_ID     = 0
SD_SCK_PIN    = 18
SD_MOSI_PIN   = 19
SD_MISO_PIN   = 16
SD_CS_PIN     = 17

LOG_FILENAME    = "datalog.csv"
LOG_MAX_LINES   = 10000
LOG_FLASH_DIR   = "/logs"
LOG_BUFFER_SIZE = 10

# ─── LED d'état ──────────────────────────────────────────────────────────────
LED_USE_BUILTIN = True    # True = LED CYW43 du Pico W (fonctionne sur les 2 cartes)

# ─── IA / Détection d'anomalie ───────────────────────────────────────────────
AI_WINDOW_SIZE    = 20
AI_ZSCORE_THRESH  = 2.5
AI_MIN_SAMPLES    = 5
AI_TREND_WINDOW   = 10
AI_ALERT_COOLDOWN = 30

# ─── Dashboard web ───────────────────────────────────────────────────────────
GRAPH_MAX_POINTS    = 60
REFRESH_INTERVAL_MS = 2000
UNITS_TEMP          = "°C"
DEVICE_NAME         = f"{USER_INITIALS} — Pico W JDEV"

# ─── Mode démo / simulation ──────────────────────────────────────────────────
WEB_DEMO_MODE = False

# ─── Asyncio — périodes des tâches ───────────────────────────────────────────
TASK_SENSOR_MS  = int(1000 / SAMPLE_RATE_HZ)
TASK_STORAGE_MS = 5000
TASK_AI_MS      = int(1000 / SAMPLE_RATE_HZ)
TASK_LED_MS     = 500
TASK_WEB_MS     = 0

# ─── Debug ───────────────────────────────────────────────────────────────────
DEBUG          = True
LOG_TO_CONSOLE = True
