# JDEV2026 — MicroPython sur Pico W
# Auteur : Eric Duvieilbourg — CNRS / LEMAR
# Usage pédagogique JDEV2026 : voir LICENSE_CODE_JDEV2026.md

import sys
sys.path.append('/JDEV2026')
sys.path.append('/JDEV2026/lib')
sys.path.append('/JDEV2026/steps/03_code_structure')
sys.path.append('/JDEV2026/steps/07_ia_zscore')

import utime
from module_acquisition import init_sensor, read_sensor
from anomaly import RollingZScore

sensor = init_sensor()
detector = RollingZScore(window=20, threshold=2.5, min_samples=8)

print("\n=== Étape 7 — détection d'anomalie z-score ===")
print("Attendez la baseline, puis soufflez sur le capteur.")
print("Ce n'est pas un modèle prédictif : c'est un détecteur statistique embarqué.")

count = 0
while True:
    count += 1
    temp, hum = read_sensor(sensor)
    anomaly = detector.push(temp)
    flag = " ⚠ ANOMALIE" if anomaly else ""
    print(f"{count:03d} | T={temp:.2f} °C | mean={detector.mean:.2f} | "
          f"sigma={detector.std:.3f} | z={detector.last_z:.2f}{flag}")
    utime.sleep(1)
