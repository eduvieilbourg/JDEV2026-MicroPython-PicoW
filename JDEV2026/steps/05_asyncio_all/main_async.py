# JDEV2026 — MicroPython sur Pico W
# Auteur : Eric Duvieilbourg — CNRS / LEMAR
# Usage pédagogique JDEV2026 : voir LICENSE_CODE_JDEV2026.md

import sys
sys.path.append('/JDEV2026')
sys.path.append('/JDEV2026/lib')
sys.path.append('/JDEV2026/steps/05_asyncio_all')

from machine import Pin
import uasyncio as asyncio
import utime
import gc

from acquisition_async import init_sensor, read_sensor_async, print_memory


led = Pin('LED', Pin.OUT)
sensor = init_sensor()


async def blink(period_ms=200):
    while True:
        led.toggle()
        await asyncio.sleep_ms(period_ms)


async def log_sensor(period_ms=2000):
    count = 0
    next_time = utime.ticks_ms()

    while True:
        count += 1

        t0 = utime.ticks_ms()
        temp, hum = await read_sensor_async(sensor)
        dt = utime.ticks_diff(utime.ticks_ms(), t0)

        print(f"{count:03d} | T={temp:.2f} °C | H={hum:.1f} % | lecture={dt} ms")

        if count % 20 == 0:
            gc.collect()

        next_time = utime.ticks_add(next_time, period_ms)
        delay = utime.ticks_diff(next_time, utime.ticks_ms())

        if delay > 0:
            await asyncio.sleep_ms(delay)
        else:
            print("⚠ retard acquisition :", -delay, "ms")
            next_time = utime.ticks_ms()
            await asyncio.sleep_ms(0)


async def main():
    print("\n=== Étape 5 — uasyncio : all  ===")
    print("Exercice : changez blink(200) en blink(50)")
    print_memory("Mémoire libre au démarrage :")
    # await asyncio.gather(blink(200), log_sensor(2000))
    await asyncio.gather(blink(25), log_sensor(500))


try:
    asyncio.run(main())

except KeyboardInterrupt:
    print("\nArrêt demandé par l'utilisateur")

finally:
    gc.collect()
    print_memory("Mémoire libre après arrêt :")