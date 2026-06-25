# JDEV2026 — MicroPython sur Pico W
# Auteur : Eric Duvieilbourg — CNRS / LEMAR
# Usage pédagogique JDEV2026 : voir LICENSE_CODE_JDEV2026.md
# =============================================================================
#  led_status.py — Gestion de la LED d'état (CYW43 du Pico W)
#  Fonctionne identiquement sur Maker Pi Pico et Pico Bricks (les deux
#  utilisent un Pico W, donc la même LED CYW43 intégrée).
# =============================================================================

import utime
import config

try:
    from machine import Pin
    if config.LED_USE_BUILTIN:
        _led = Pin("LED", Pin.OUT)
    else:
        _led = Pin(25, Pin.OUT)
except Exception:
    _led = None


def _set(state):
    if _led:
        try:
            _led.value(state)
        except Exception:
            pass


def on():  _set(1)
def off(): _set(0)
def toggle():
    if _led:
        try:
            _led.toggle()
        except Exception:
            pass


def startup_sequence():
    for _ in range(3):
        on();  utime.sleep_ms(100)
        off(); utime.sleep_ms(100)
    utime.sleep_ms(200)


async def task_led(shared_data, ai_state):
    import uasyncio as asyncio
    period_ms = config.TASK_LED_MS

    while True:
        if not shared_data.get("valid", False):
            on()
            await asyncio.sleep_ms(period_ms)
            continue

        anomaly = ai_state.get("anomaly", False) if ai_state else False
        current_period = 100 if anomaly else period_ms

        toggle()
        await asyncio.sleep_ms(current_period)
