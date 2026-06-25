# =============================================================================
#  lib/picobricks_sensors.py
#  Extrait allégé de picobricks.py (Robotistan) — UNIQUEMENT les capteurs
#  température/humidité utilisés dans l'atelier JDEV2026 :
#    - SHTC3  : capteur I2C (Pico Bricks version ≥ juillet 2024)
#    - DHT11  : capteur 1-fil (Pico Bricks version < juillet 2024, GP11)
#
#  Source originale : picobricks.py fourni par Eric DUVIEILBOURG (Robotistan)
#  Code DHT11 sous-jacent : Author peterhinch (mentionné dans le fichier source)
#  Allégé pour l'atelier — MFRC522, WS2812, MotorDriver, IR_RX retirés
#  (non utilisés pour la partie capteur température/humidité).
# =============================================================================

import utime
import array
import micropython
from micropython import const
from machine import Pin


# ─────────────────────────────────────────────────────────────────────────────
#  SHTC3 — capteur I2C (Pico Bricks version récente, adresse fixe 0x70)
#  Protocole Sensirion par commandes brutes (pas de registres standards)
# ─────────────────────────────────────────────────────────────────────────────
class SHTC3:
    """
    Driver SHTC3 — identique à la version officielle picobricks.py.
    Adresse I2C fixe : 0x70 (non configurable, propre au capteur).
    """
    I2C_ADDR = 0x70

    def __init__(self, i2c):
        buf  = bytearray(2)
        buf1 = bytearray(3)

        self.i2c = i2c
        # Wake-up command
        buf[0] = 0x35
        buf[1] = 0x17
        self.i2c.writeto(self.I2C_ADDR, buf, False)
        utime.sleep_ms(500)
        # Read ID command (vérifie la présence du capteur)
        buf[0] = 0xEF
        buf[1] = 0xC8
        self.i2c.writeto(self.I2C_ADDR, buf, False)
        utime.sleep_ms(500)
        self.i2c.readfrom_into(self.I2C_ADDR, buf1, True)

    def temperature(self):
        buf  = bytearray(2)
        buf1 = bytearray(2)
        buf[0] = 0x78
        buf[1] = 0x66
        self.i2c.writeto(self.I2C_ADDR, buf, False)
        utime.sleep_ms(100)
        self.i2c.readfrom_into(self.I2C_ADDR, buf1, True)
        utime.sleep_ms(100)
        _temperature = (buf1[0] << 8) | buf1[1]
        _temperature = (((4375 * _temperature) >> 14) - 4500) / 100
        return _temperature

    def humidity(self):
        buf  = bytearray(2)
        buf1 = bytearray(5)
        buf[0] = 0x78
        buf[1] = 0x66
        self.i2c.writeto(self.I2C_ADDR, buf, False)
        utime.sleep_ms(100)
        self.i2c.readfrom_into(self.I2C_ADDR, buf1, True)
        utime.sleep_ms(100)
        _humidity = (buf1[3] << 8) | buf1[4]
        _humidity = ((625 * _humidity) >> 12) / 100
        return _humidity

    def measure(self):
        """
        Compatibilité avec l'API SHT30 utilisée ailleurs dans le projet :
        retourne (temp, hum) en un seul appel, comme sensor.measure().
        """
        return self.temperature(), self.humidity()


# ─────────────────────────────────────────────────────────────────────────────
#  DHT11 — capteur 1-fil (Pico Bricks version < juillet 2024, GP11)
#  Code identique à la version officielle picobricks.py
# ─────────────────────────────────────────────────────────────────────────────
class InvalidChecksum(Exception):
    pass


class InvalidPulseCount(Exception):
    pass


_MAX_UNCHANGED   = const(100)
_MIN_INTERVAL_US = const(200000)   # 200ms minimum entre 2 mesures
_HIGH_LEVEL      = const(50)
_EXPECTED_PULSES = const(84)


class DHT11:
    """
    Driver DHT11 — identique à la version officielle picobricks.py.
    Connexion : 1 seule broche de données (pas d'I2C).
    Limite matérielle : pas plus d'une mesure toutes les 200ms.
    measure() lève InvalidChecksum ou InvalidPulseCount en cas d'erreur
    de lecture — À TOUJOURS encapsuler dans un try/except.
    """
    _temperature: float
    _humidity: float

    def __init__(self, pin):
        self._pin = pin
        self._last_measure = utime.ticks_us()
        self._temperature = -1
        self._humidity = -1

    def measure(self):
        current_ticks = utime.ticks_us()
        if utime.ticks_diff(current_ticks, self._last_measure) < _MIN_INTERVAL_US and (
            self._temperature > -1 or self._humidity > -1
        ):
            # Moins de 200ms depuis la dernière lecture — trop tôt
            return

        self._send_init_signal()
        pulses = self._capture_pulses()
        buffer = self._convert_pulses_to_buffer(pulses)
        self._verify_checksum(buffer)

        self._humidity    = buffer[0] + buffer[1] / 10
        self._temperature = buffer[2] + buffer[3] / 10
        self._last_measure = utime.ticks_us()

    @property
    def humidity(self):
        return self._humidity

    @property
    def temperature(self):
        return self._temperature

    def _send_init_signal(self):
        self._pin.init(Pin.OUT, Pin.PULL_DOWN)
        self._pin.value(1)
        utime.sleep_ms(50)
        self._pin.value(0)
        utime.sleep_ms(25)

    @micropython.native
    def _capture_pulses(self):
        pin = self._pin
        pin.init(Pin.IN, Pin.PULL_UP)

        val = 1
        idx = 0
        transitions = bytearray(_EXPECTED_PULSES)
        unchanged = 0
        timestamp = utime.ticks_us()

        while unchanged < _MAX_UNCHANGED:
            if val != pin.value():
                if idx >= _EXPECTED_PULSES:
                    raise InvalidPulseCount(
                        "Got more than {} pulses".format(_EXPECTED_PULSES)
                    )
                now = utime.ticks_us()
                transitions[idx] = now - timestamp
                timestamp = now
                idx += 1
                val = 1 - val
                unchanged = 0
            else:
                unchanged += 1
        pin.init(Pin.OUT, Pin.PULL_DOWN)
        if idx != _EXPECTED_PULSES:
            raise InvalidPulseCount(
                "Expected {} but got {} pulses".format(_EXPECTED_PULSES, idx)
            )
        return transitions[4:]

    def _convert_pulses_to_buffer(self, pulses):
        binary = 0
        for idx in range(0, len(pulses), 2):
            binary = binary << 1 | int(pulses[idx] > _HIGH_LEVEL)

        buffer = array.array("B")
        for shift in range(4, -1, -1):
            buffer.append(binary >> shift * 8 & 0xFF)
        return buffer

    def _verify_checksum(self, buffer):
        checksum = 0
        for buf in buffer[0:4]:
            checksum += buf
        if checksum & 0xFF != buffer[4]:
            raise InvalidChecksum()
