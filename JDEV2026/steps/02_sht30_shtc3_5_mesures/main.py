# JDEV2026 — MicroPython sur Pico W
# Auteur : Eric Duvieilbourg — CNRS / LEMAR
# Usage pédagogique JDEV2026 : voir LICENSE_CODE_JDEV2026.md

import sys
sys.path.append('/JDEV2026')
sys.path.append('/JDEV2026/lib')

from machine import I2C, Pin, reset
import utime
import gc

from sht30 import SHT30
from picobricks_sensors import SHTC3


# ------------------------------------------------------------
# Nettoyage mémoire au démarrage
# ------------------------------------------------------------
gc.collect()

print("\n=== Étape 2 — 5 mesures température / humidité ===")
print("Mémoire libre au démarrage :", gc.mem_free(), "octets")


# ------------------------------------------------------------
# Configuration I2C
# ------------------------------------------------------------
# SDA_PIN, SCL_PIN = 0, 1  # Marker Pico
SDA_PIN, SCL_PIN = 4, 5  # PicoBricks

SHT30_ADDRESS = 0x44
SHTC3_ADDRESS = 0x70

i2c = I2C(0, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN))

devices = i2c.scan()
print("Périphériques I2C détectés :", [hex(d) for d in devices])


# ------------------------------------------------------------
# Détection simple du capteur disponible
# ------------------------------------------------------------
sensor = None
sensor_name = None

if SHT30_ADDRESS in devices:
    try:
        sensor = SHT30(i2c, address=SHT30_ADDRESS)
        sensor_name = "SHT30 / ENV III"
        print("✓ Capteur détecté :", sensor_name)
    except Exception as e:
        print("Erreur initialisation SHT30 :", e)

elif SHTC3_ADDRESS in devices:
    try:
        sensor = SHTC3(i2c)
        sensor_name = "SHTC3 / PicoBricks"
        print("✓ Capteur détecté :", sensor_name)
    except Exception as e:
        print("Erreur initialisation SHTC3 :", e)

else:
    print("✗ Aucun capteur SHT30 ou SHTC3 détecté")



# ------------------------------------------------------------
# Mesures
# ------------------------------------------------------------
temps = []

if sensor is not None:

    try:
        for i in range(5):
            gc.collect()

            temp, hum = sensor.measure()

            temps.append(temp)

            print(f"{i+1}/5 → {temp:.2f} °C  {hum:.1f} %")
            utime.sleep_ms(1000)

        print(f"Min : {min(temps):.2f} °C")
        print(f"Max : {max(temps):.2f} °C")
        print("✓ Test terminé")

    except KeyboardInterrupt:
        print("\nArrêt demandé par l'utilisateur")

    except Exception as e:
        print("Erreur pendant la mesure :", e)

else:
    print("Test impossible : aucun capteur valide, reset dans 5s")
    utime.sleep(5)
    reset()


# ------------------------------------------------------------
# Nettoyage mémoire final
# ------------------------------------------------------------
gc.collect()
print("Mémoire libre après test :", gc.mem_free(), "octets")


# ------------------------------------------------------------
# Boucle d'attente
# évite que le programme se termine brutalement dans Thonny
# Ctrl+C permet de reprendre la main dans le REPL
# ------------------------------------------------------------
print("Programme en attente. Ctrl+C pour reprendre la main.")

try:
    while True:
        utime.sleep(1)

except KeyboardInterrupt:
    print("\nRetour au REPL")