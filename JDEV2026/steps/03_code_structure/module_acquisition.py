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


# SDA_PIN, SCL_PIN = 0, 1  # M5Stack ENV III
SDA_PIN, SCL_PIN = 4, 5  # PicoBricks Temp&Hum

I2C_ID = 0
SHTC3_ADDR = 0x70
SHT30_ADDR = 0x44


def reset_after_error(delay_s=5):
    print("Reset dans", delay_s, "secondes...")
    utime.sleep(delay_s)
    reset()


def print_memory(label="Mémoire libre :"):
    gc.collect()
    print(label, gc.mem_free(), "octets")


def init_sensor():
    """
    Initialise automatiquement le capteur disponible.

    Capteurs acceptés :
    - SHT30 / ENV III     adresse 0x44
    - SHTC3 / PicoBricks  adresse 0x70
    """

    print_memory("Mémoire libre au démarrage :")

    i2c = I2C(I2C_ID, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN))
    # i2c = I2C(I2C_ID, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=1_000_000)

    devices = i2c.scan()
    print("Périphériques I2C détectés :", [hex(d) for d in devices])

    try:
        if SHT30_ADDR in devices:
            sensor = SHT30(i2c, address=SHT30_ADDR)
            print("✓ Capteur utilisé : SHT30 / ENV III")
            return sensor

        if SHTC3_ADDR in devices:
            sensor = SHTC3(i2c)
            print("✓ Capteur utilisé : SHTC3 / PicoBricks")
            return sensor

        print("✗ Aucun capteur SHT30 ou SHTC3 détecté")
        reset_after_error()

    except Exception as e:
        print("Erreur initialisation capteur :", e)
        reset_after_error()


def read_sensor(sensor):
    """
    Lit une mesure température / humidité.
    """

    try:
        # gc.collect()
        return sensor.measure()

    except Exception as e:
        print("Erreur lecture capteur :", e)
        reset_after_error()


if __name__ == "__main__":
    print("\n=== Test direct du module_acquisition.py ===")

    sensor = init_sensor()

    for i in range(5):
        temp, hum = read_sensor(sensor)
        print(f"{i+1}/5 → {temp:.2f} °C  {hum:.1f} %")
        utime.sleep(1)

    print_memory("Mémoire libre après test :")
    print("✓ Test direct terminé")

