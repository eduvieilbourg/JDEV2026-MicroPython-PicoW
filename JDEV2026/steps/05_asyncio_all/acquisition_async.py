# JDEV2026 — MicroPython sur Pico W
# Auteur : Eric Duvieilbourg — CNRS / LEMAR
# Usage pédagogique JDEV2026 : voir LICENSE_CODE_JDEV2026.md

import sys
sys.path.append('/JDEV2026')
sys.path.append('/JDEV2026/lib')
sys.path.append('/JDEV2026/steps/05_asyncio_all')

from machine import I2C, Pin, reset
import utime
import gc

from sht30_async import SHT30_ASYNC as SHT30
from shtc3_async import SHTC3_ASYNC as SHTC3


SDA_PIN, SCL_PIN = 4, 5
I2C_ID = 0

SHT30_ADDR = 0x44     # M5Stack ENV III
SHTC3_ADDR = 0x70     # PicoBricks


def reset_after_error(delay_s=5):
    print("Reset dans", delay_s, "secondes...")
    utime.sleep(delay_s)
    reset()


def print_memory(label="Mémoire libre :"):
    gc.collect()
    print(label, gc.mem_free(), "octets")


def init_sensor():
    gc.collect()

    i2c = I2C(
        I2C_ID,
        sda=Pin(SDA_PIN),
        scl=Pin(SCL_PIN))  # , freq=400000)

    devices = i2c.scan()
    print("Périphériques I2C détectés :", [hex(d) for d in devices])

    try:
        if SHT30_ADDR in devices:
            print("✓ Capteur utilisé : AsyncioSHT30 / ENV III")
            return SHT30(i2c, address=SHT30_ADDR)

        if SHTC3_ADDR in devices:
            print("✓ Capteur utilisé : AsyncioSHTC3 / PicoBricks")
            return SHTC3(i2c)

        print("✗ Aucun capteur SHT30 ou SHTC3 détecté")
        reset_after_error()

    except Exception as e:
        print("Erreur initialisation capteur :", e)
        reset_after_error()


def read_sensor(sensor):
    """
    Lecture synchrone classique.
    Compatible avec les tests simples.
    """
    try:
        return sensor.measure()

    except Exception as e:
        print("Erreur lecture capteur :", e)
        reset_after_error()


async def read_sensor_async(sensor):
    """
    Lecture uasyncio.

    Ici, les capteurs initialisés par init_sensor() possèdent
    tous une méthode measure_async().
    """
    try:
        return await sensor.measure_async()

    except Exception as e:
        print("Erreur lecture capteur async :", e)
        reset_after_error()


if __name__ == "__main__":
    print("\n=== Test direct acquisition_async.py ===")

    sensor = init_sensor()

    for i in range(5):
        t0 = utime.ticks_ms()
        temp, hum = read_sensor(sensor)
        dt = utime.ticks_diff(utime.ticks_ms(), t0)

        print(f"{i+1}/5 → {temp:.2f} °C  {hum:.1f} % | lecture={dt} ms")
        utime.sleep(1)

    print_memory("Mémoire libre après test :")
    print("✓ Test direct terminé")