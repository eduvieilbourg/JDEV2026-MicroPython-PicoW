# JDEV2026 — MicroPython sur Pico W
# Auteur : Eric Duvieilbourg — CNRS / LEMAR
# Usage pédagogique JDEV2026 : voir LICENSE_CODE_JDEV2026.md

import sys
sys.path.append('/JDEV2026/lib')

import utime
import uasyncio as asyncio

from picobricks_sensors import SHTC3


class SHTC3_ASYNC(SHTC3):
    """
    Version uasyncio du driver SHTC3.

    On hérite du driver SHTC3 existant, mais on ajoute une méthode
    measure_async() adaptée à uasyncio.

    Objectifs :
    - ne pas modifier le driver PicoBricks d'origine ;
    - éviter les sleep_ms(100) bloquants ;
    - faire température + humidité en une seule acquisition.
    """

    I2C_ADDR = 0x70

    CMD_WAKEUP = b'\x35\x17'
    CMD_MEASURE_T_RH = b'\x78\x66'   # mesure T puis RH, sans clock stretching


    def __init__(self, i2c):
        # On ne reprend pas le __init__ du driver d'origine,
        # car il contient deux sleep_ms(500).
        self.i2c = i2c
        self.buf = bytearray(6)

        self.i2c.writeto(self.I2C_ADDR, self.CMD_WAKEUP)
        utime.sleep_ms(2)
        

    def _convert(self):
        raw_temp = (self.buf[0] << 8) | self.buf[1]
        raw_hum = (self.buf[3] << 8) | self.buf[4]

        temp = -45.0 + 175.0 * raw_temp / 65535.0
        hum = 100.0 * raw_hum / 65535.0

        if hum < 0.0:
            hum = 0.0
        elif hum > 100.0:
            hum = 100.0

        return temp, hum


    async def measure_async(self):
        self.i2c.writeto(self.I2C_ADDR, self.CMD_WAKEUP)
        await asyncio.sleep_ms(1)

        self.i2c.writeto(self.I2C_ADDR, self.CMD_MEASURE_T_RH)

        # Temps de conversion capteur.
        # En asyncio, on ne bloque pas les autres tâches.
        await asyncio.sleep_ms(20)

        self.i2c.readfrom_into(self.I2C_ADDR, self.buf)

        return self._convert()


    def measure(self):
        """
        Version synchrone optimisée, utile si on teste ce module directement.
        """

        self.i2c.writeto(self.I2C_ADDR, self.CMD_WAKEUP)
        utime.sleep_ms(1)

        self.i2c.writeto(self.I2C_ADDR, self.CMD_MEASURE_T_RH)
        utime.sleep_ms(20)

        self.i2c.readfrom_into(self.I2C_ADDR, self.buf)

        return self._convert()