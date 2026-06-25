# Workflow GitHub conseillé — JDEV2026

## Option recommandée pour l'atelier

1. Créer un dépôt `JDEV2026-MicroPython-PicoW`.
2. Le rendre public uniquement pendant la durée des JDEV.
3. Ajouter dans le README : licence, attribution, chemin Thonny à ouvrir, tags par étape.
4. Après l'atelier, soit le laisser public, soit le passer privé en sachant que les forks créés pendant la période publique peuvent rester publics.

## Tags utiles

```bash
git init
git add .
git commit -m "JDEV2026 progressive workshop package"

git tag step-01-i2c-scan
git tag step-02-sht30-5-mesures
git tag step-03-code-structure
git tag step-04-timing-ticks
git tag step-05-asyncio
git tag step-06-web-api
git tag step-07-ia-zscore
git tag final

git remote add origin git@github.com:USER/JDEV2026-MicroPython-PicoW.git
git push -u origin main --tags
```

## Récupération côté participant

Simple : bouton **Code → Download ZIP**, puis copier le dossier `JDEV2026` sur le Pico via Thonny.

Plus avancé :

```bash
git clone https://github.com/USER/JDEV2026-MicroPython-PicoW.git
cd JDEV2026-MicroPython-PicoW
```
