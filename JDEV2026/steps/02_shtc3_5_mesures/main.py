# JDEV2026 — MicroPython sur Pico W
# Auteur : Eric Duvieilbourg — CNRS / LEMAR
# Usage pédagogique JDEV2026 : voir LICENSE_CODE_JDEV2026.md

import sys
sys.path.append('/JDEV2026')
sys.path.append('/JDEV2026/lib')

import time
from machine import Pin, I2C, reset
import gc
# from picobricks import SHTC3
from lib.picobricks_sensors import SHTC3

# Maker Pi Pico + M5Stack ENV III : GP0=SDA, GP1=SCL
# Pico Bricks I2C récent + SHTC3 : changez en GP4/GP5 si besoin
#SDA_PIN, SCL_PIN = 0, 1  # Marker Pico
SDA_PIN, SCL_PIN = 4, 5  # PicoBricks
CONTINUE = False

gc.collect()

i2c = I2C(0, sda=SDA_PIN, scl=SCL_PIN)

try:
    sensor = SHTC3(i2c)
    CONTINUE = True
except Exception as err:
    print(err)
    del(i2c)
    gc.collect()
    time.sleep(2)
    reset()
    
    

if CONTINUE:
    temps = []
    
    for i in range(5):
        temp, hum = sensor.temperature(), sensor.humidity()
        temps.append(temp)
        print(f"{i+1}/5 → {temp:.2f} °C")
        
    print(f'min: {min(temps)}°C, max: {max(temps)}°C')

    del(i2c)


