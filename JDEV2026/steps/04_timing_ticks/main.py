# JDEV2026 — MicroPython sur Pico W
# Auteur : Eric Duvieilbourg — CNRS / LEMAR
# Usage pédagogique JDEV2026 : voir LICENSE_CODE_JDEV2026.md

import sys
sys.path.append('/JDEV2026')
sys.path.append('/JDEV2026/lib')
sys.path.append('/JDEV2026/steps/03_code_structure')

import utime
from module_acquisition import init_sensor, read_sensor

PERIOD_MS = 1000
N = 10

print("\n=== Étape 4 — timing robuste avec ticks_ms() ===")
sensor = init_sensor()
t_next = utime.ticks_ms()
t_start = None

try:
    for i in range(N):
        start = utime.ticks_ms()
        if not i: t_start = start
        temp, hum = read_sensor(sensor)
        
        elapsed = utime.ticks_diff(utime.ticks_ms(), start)
        print(f"{i+1:02d} | {temp:.2f} °C | durée mesure={elapsed} ms")
        
        t_next = utime.ticks_add(t_next, PERIOD_MS)
        delay = utime.ticks_diff(t_next, utime.ticks_ms())
        
        if delay > 0: utime.sleep_ms(delay)

    print(f"✓ Période tenue {t_next} - {t_start} sans accumuler la durée de mesure")
    print("✓ Test terminé")

except KeyboardInterrupt:
    print("\nArrêt demandé par l'utilisateur")

