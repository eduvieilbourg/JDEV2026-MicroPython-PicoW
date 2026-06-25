# JDEV2026 — MicroPython sur Pico W
# Auteur : Eric Duvieilbourg — CNRS / LEMAR
# Usage pédagogique JDEV2026 : voir LICENSE_CODE_JDEV2026.md

import sys
sys.path.append('/JDEV2026')
sys.path.append('/JDEV2026/lib')
sys.path.append('/JDEV2026/steps/03_code_structure')
 
import utime

from module_acquisition import init_sensor, read_sensor, print_memory


print("\n=== Étape 3 — code structuré ===")

sensor = init_sensor()
temps = []

try:
    for i in range(10):
        temp, hum = read_sensor(sensor)
        temps.append(temp)

        print(f"{i+1:02d} | T={temp:.2f} °C | H={hum:.1f} %")
        utime.sleep(1)

    print()
    print(f"Min : {min(temps):.2f} °C")
    print(f"Max : {max(temps):.2f} °C")
    print("✓ Test terminé")

except KeyboardInterrupt:
    print("\nArrêt demandé par l'utilisateur")

print_memory("Mémoire libre après test :")
print("✓ module_acquisition.py est maintenant réutilisable")
