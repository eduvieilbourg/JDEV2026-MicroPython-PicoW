# JDEV2026 — MicroPython sur Raspberry Pi Pico W

Atelier pratique JDEV2026 — **du Python sur microcontrôleur**, par Eric Duvieilbourg (CNRS / LEMAR).

Objectif : construire progressivement un mini-datalogger embarqué : capteur I2C, acquisition propre, timing robuste, `uasyncio`, serveur web local, API REST et détection d'anomalie légère.

## Support de présentation

- [Support PDF](supports/Atelier_MicroPython_Pico_W_beta.pdf)

Le code à copier sur le Pico W se trouve dans le dossier :

```text
JDEV2026/
```

## Démarrage rapide Thonny

Pour l’atelier :
1. Télécharger le dépôt
2. Copier le dossier complet JDEV2026/ sur le Pico W
3. Repérer les scripts dans JDEV2026/steps/
4. À la fin de chaque partie dans la présentation, lancer et tester le fichier indiqué.

## Parcours progressif

| Partie | Fichier à ouvrir dans Thonny | Ce que l'on valide |
|---|---|---|
| 1 | `JDEV2026/steps/01_i2c_scan/main.py` | Le capteur répond sur le bus I2C |
| 2 | `JDEV2026/steps/02_sht30_5_mesures/main.py` | 5 mesures + min/max |
| 2 | `JDEV2026/steps/02_shtc3_5_mesures/main.py` | 5 mesures + min/max |
| 2 | `JDEV2026/steps/02_sht30_shtc3_5_mesures/main.py` | 5 mesures + min/max |
| 3 | `JDEV2026/steps/03_code_structure/main.py` | Code découpé en fonctions/modules |
| 4 | `JDEV2026/steps/04_timing_ticks/main.py` | Boucle périodique sans dérive cumulative |
| 5 | `JDEV2026/steps/05_asyncio_led_capteur/main.py` | Deux tâches coopératives : LED + capteur |
| 5 | `JDEV2026/steps/05_asyncio_all/*.py` | Toutes les tâches timer sont coopératives  |
| 6 | `JDEV2026/steps/06_web_api/main.py` | WiFi AP + routes `/`, `/data`, `/temp` |
| 7 | `JDEV2026/steps/07_ia_zscore/main.py` | Détection statistique d'anomalie par z-score |
| Final | `JDEV2026/main.py` | Application complète : dashboard, stockage, IA, API |

## Organisation du dépôt

```text
JDEV2026-MicroPython-PicoW/
├── README.md
├── NOTICE
├── LICENSE_CODE_JDEV2026.md
├── LICENSE_SUPPORTS_CC-BY-NC-ND-4.0.md
├── CITATION.cff
├── .zenodo.json
├── .gitignore
│
├── JDEV2026/                 ← seul dossier à copier sur le Pico
│   ├── main.py               # application finale à lancer
│   ├── config.py             # configuration globale
│   ├── acquisition.py        # auto-détection capteurs + acquisition
│   ├── web_ap.py             # WiFi AP + serveur HTTP/API REST
│   ├── storage_sdcard.py     # CSV + SD si disponible
│   ├── led_status.py         # état des leds du projet
│   ├── ai/                   # statistiques, z-score, tendance, alertes
│   ├── lib/                  # drivers SHT30 / SD / Pico Bricks
│   ├── static/               # dashboard HTML
│   └── steps/                # étapes pédagogiques autonomes
│
├── supports/
│   ├── JDEV2026_MicroPython_Pico_W.pdf    # présentation atelier
│
└── docs/
    ├── QR_GitHub.png
    └── screenshots/
```

## Point important sur l'IA

Dans cet atelier, le mot IA est utilisé mais sans rigueur :

- le Pico W ne fait pas tourner un LLM ;
- le z-score glissant n'est pas un modèle prédictif ;
- c'est un **détecteur statistique embarqué** utile pour introduire l'edge AI ;
- la suite logique est TinyML / TFLite Micro / Edge Impulse, mais ce n'est pas l'objet des 2h.

## GitHub conseillé pour l'atelier

Pour 20 participants, le plus fluide est : dépôt public pendant les JDEV, avec un `README` clair. Par la suite il y aura des tags/branches par étape :

```bash
git tag step-01-i2c-scan
git tag step-02-sht30-5-mesures
git tag step-03-code-structure
git tag step-04-timing-ticks
git tag step-05-asyncio
git tag step-06-web-api
git tag step-07-ia-zscore
git tag final
```

Ou alternative plus contrôlée : dépôt privé dans une organisation GitHub avec une équipe `jdev2026-participants` en lecture. 
Éviter le dépôt privé d'un compte personnel pour du read-only propre pour les participants.

## Licence

Voir :

- `LICENSE_CODE_JDEV2026.md` pour le code ;
- `LICENSE_SUPPORTS_CC-BY-NC-ND-4.0.md` pour les supports pédagogiques.
