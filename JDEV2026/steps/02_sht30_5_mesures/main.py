# JDEV2026 — MicroPython sur Pico W
# Auteur : Eric Duvieilbourg — CNRS / LEMAR
# Usage pédagogique JDEV2026 : voir LICENSE_CODE_JDEV2026.md

import sys
sys.path.append('/JDEV2026')
sys.path.append('/JDEV2026/lib')

from machine import I2C, Pin
import utime
from sht30 import SHT30
from picobricks_sensors import SHTC3

SDA_PIN = 0
SCL_PIN = 1
ADDRESS = 0x44

print("\n=== Étape 2 — 5 mesures SHT30 ===")
i2c = I2C(0, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN))

try:
    sensor = SHT30(i2c, address=ADDRESS)
    print('sht30 ok')
except:
    sensor = None
    print('sht30 erreur')

try:
    sensor = SHTC3(i2c)
    print('shtc3 ok')
except:
    sensor = None
    print('shtc3 erreur')
    

    

temps = []
for i in range(5):
    if sensor:
        temp, hum = sensor.measure()

    temps.append(temp)
    print(f"{i+1}/5 → {temp:.2f} °C  {hum:.1f} %")
    utime.sleep_ms(1000)

print(f"Min : {min(temps):.2f} °C")
print(f"Max : {max(temps):.2f} °C")
print("✓ Test terminé")

while True:
    utime.sleep(1)
