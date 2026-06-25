# =============================================================================
#  lib/sht30.py — Driver MicroPython pour le capteur SHT30 (Sensirion)
#  Compatible M5Stack ENV III, Adafruit SHT30, Grove SHT30
#  Protocole : I2C, adresse 0x44 (défaut) ou 0x45
# =============================================================================

import utime


class SHT30Error(Exception):
    pass


class SHT30:
    """
    Driver léger pour SHT30.
    Utilise la commande High Repeatability (0x2400, sans clock-stretching).
    """

    CMD_MEASURE_HIGH = b'\x24\x00'
    CMD_SOFT_RESET   = b'\x30\xA2'
    CMD_STATUS       = b'\xF3\x2D'
    CMD_CLEAR_STATUS = b'\x30\x41'
    CMD_HEATER_ON    = b'\x30\x6D'
    CMD_HEATER_OFF   = b'\x30\x66'

    def __init__(self, i2c, address=0x44):
        self._i2c  = i2c
        self._addr = address
        self._buf  = bytearray(6)
        self._check_presence()

    def _check_presence(self):
        devices = self._i2c.scan()
        if self._addr not in devices:
            raise SHT30Error(
                f"SHT30 non trouvé à l'adresse 0x{self._addr:02X}. "
                f"Appareils détectés : {[hex(d) for d in devices]}"
            )

    @staticmethod
    def _crc8(data):
        crc = 0xFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                crc = (crc << 1) ^ 0x31 if crc & 0x80 else crc << 1
                crc &= 0xFF
        return crc

    def measure(self):
        """
        Lance une mesure et retourne (temperature_C, humidity_pct).
        Lève SHT30Error si le CRC est invalide.
        """
        self._i2c.writeto(self._addr, self.CMD_MEASURE_HIGH)
        utime.sleep_ms(20)
        self._i2c.readfrom_into(self._addr, self._buf)

        raw_temp = (self._buf[0] << 8) | self._buf[1]
        raw_hum  = (self._buf[3] << 8) | self._buf[4]

        if self._crc8(self._buf[0:2]) != self._buf[2]:
            raise SHT30Error("CRC température invalide")
        if self._crc8(self._buf[3:5]) != self._buf[5]:
            raise SHT30Error("CRC humidité invalide")

        temp = -45.0 + 175.0 * raw_temp / 65535.0
        hum  = 100.0 * raw_hum  / 65535.0
        hum  = max(0.0, min(100.0, hum))

        return round(temp, 2), round(hum, 2)

    def reset(self):
        self._i2c.writeto(self._addr, self.CMD_SOFT_RESET)
        utime.sleep_ms(2)

    def heater(self, on=True):
        cmd = self.CMD_HEATER_ON if on else self.CMD_HEATER_OFF
        self._i2c.writeto(self._addr, cmd)

    def status(self):
        self._i2c.writeto(self._addr, self.CMD_STATUS)
        utime.sleep_ms(1)
        buf = bytearray(3)
        self._i2c.readfrom_into(self._addr, buf)
        return (buf[0] << 8) | buf[1]
