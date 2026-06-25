# JDEV2026 — MicroPython sur Pico W
# Auteur : Eric Duvieilbourg — CNRS / LEMAR
# Usage pédagogique JDEV2026 : voir LICENSE_CODE_JDEV2026.md

import sys
sys.path.append('/JDEV2026')
sys.path.append('/JDEV2026/lib')
sys.path.append('/JDEV2026/steps/03_code_structure')

from machine import Pin
import uasyncio as asyncio
from module_acquisition import init_sensor, read_sensor

led = Pin('LED', Pin.OUT)
sensor = init_sensor()

async def blink(period_ms=200):
    while True:
        led.toggle()
        await asyncio.sleep_ms(period_ms)

async def log_sensor(period_s=2):
    count = 0
    while True:
        count += 1
        temp, hum = read_sensor(sensor)
        print(f"{count:03d} | T={temp:.2f} °C | H={hum:.1f} %")
        await asyncio.sleep(period_s)

async def main():
    print("\n=== Étape 5 — uasyncio : LED + capteur ===")
    print("Exercice : changez blink(200) en blink(50)")
    # await asyncio.gather(blink(200), log_sensor(2))
    await asyncio.gather(blink(50), log_sensor(1))

try:
    asyncio.run(main())

except KeyboardInterrupt:
    print("\nArrêt demandé par l'utilisateur")

finally:
    gc.collect()
    print_memory("Mémoire libre après arrêt :")