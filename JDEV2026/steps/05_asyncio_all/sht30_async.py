# JDEV2026 — MicroPython sur Pico W
# Auteur : Eric Duvieilbourg — CNRS / LEMAR
# Usage pédagogique JDEV2026 : voir LICENSE_CODE_JDEV2026.md

import sys
sys.path.append('/JDEV2026/lib')

import utime
import uasyncio as asyncio

from sht30 import SHT30


class SHT30_ASYNC(SHT30):
    """
    Version uasyncio du driver SHT30 (héritage)

    On hérite du driver SHT30 existant, mais on ajoute une méthode
    measure_async() qui respecte la logique coopérative de uasyncio.

    Le principe :
    - l'écriture I2C reste synchrone ;
    - la lecture I2C reste synchrone ;
    - le temps d'attente du capteur devient non bloquant.
    """

    CMD_MEASURE_HIGH_REPEATABILITY = b'\x24\x00'

    @staticmethod
    def _convert(data):
        """
        Convertit les 6 octets retournés par le SHT30.

        Format :
        - data[0:2] : température brute
        - data[2]   : CRC température
        - data[3:5] : humidité brute
        - data[5]   : CRC humidité
        """
        raw_temp = (data[0] << 8) | data[1]
        raw_hum = (data[3] << 8) | data[4]

        temp = -45.0 + 175.0 * raw_temp / 65535.0
        hum = 100.0 * raw_hum / 65535.0

        if hum < 0.0:
            hum = 0.0
        elif hum > 100.0:
            hum = 100.0

        return temp, hum


    def measure(self):
        """
        Version synchrone optimisée.

        Elle permet de tester ce module sans uasyncio avec _convert
        """
        self.i2c.writeto(self.address, self.CMD_MEASURE_HIGH_REPEATABILITY)

        # Attente bloquante classique.
        utime.sleep_ms(20)

        data = self.i2c.readfrom(self.address, 6)

        return self._convert(data)


    async def measure_async(self):
        """
        Version uasyncio.

        La différence importante est ici :

            await asyncio.sleep_ms(20)

        Pendant ce temps, les autres tâches peuvent continuer :
        LED, serveur web, affichage, etc.
        """
        self.i2c.writeto(self.address, self.CMD_MEASURE_HIGH_REPEATABILITY)

        # Temps de conversion du capteur.
        # Avec await, on rend la main au scheduler uasyncio.
        await asyncio.sleep_ms(20)

        # La transaction I2C reste synchrone, mais elle est courte.
        data = self.i2c.readfrom(self.address, 6)

        return self._convert(data)