# =============================================================================
#  lib/sdcard.py — Driver MicroPython pour carte SD via SPI
#  Basé sur le driver officiel MicroPython (MIT License)
# =============================================================================

from machine import SPI, Pin
import utime

_CMD_TIMEOUT = const(100)
_R1_IDLE_STATE = const(1 << 0)
_TOKEN_DATA = const(0xFE)


class SDCard:
    def __init__(self, spi, cs, baudrate=1_000_000):
        self.spi = spi
        self.cs  = cs
        self.cmdbuf = bytearray(6)
        self.dummybuf = bytearray(512)
        for i in range(512):
            self.dummybuf[i] = 0xFF
        self.dummybuf_memoryview = memoryview(self.dummybuf)

        self.cs.init(self.cs.OUT, value=1)
        self.spi.init(baudrate=400_000, phase=0, polarity=0)
        self._init_card(baudrate)

    def _init_card(self, baudrate):
        for _ in range(10):
            self.spi.write(b'\xff')

        self.cs(0)
        r = self.cmd(0, 0, 0x95)
        if r != _R1_IDLE_STATE:
            raise OSError("SD : échec CMD0")

        r = self.cmd(8, 0x01AA, 0x87, 4)
        if r == _R1_IDLE_STATE:
            self._init_card_v2()
        else:
            self._init_card_v1()

        self.spi.init(baudrate=baudrate, phase=0, polarity=0)
        self.sectors = self.cmd(9, 0, 0, 16, True)
        if isinstance(self.sectors, int):
            if self.sectors < 0:
                raise OSError("SD : échec lecture CSD")
            self.sectors = self._parse_csd(bytearray(16))

    def _init_card_v1(self):
        for _ in range(_CMD_TIMEOUT):
            self.cmd(55, 0, 0)
            r = self.cmd(41, 0, 0)
            if r == 0:
                self._sdhc = False
                return
            utime.sleep_ms(10)
        raise OSError("SD v1 : timeout ACMD41")

    def _init_card_v2(self):
        for _ in range(_CMD_TIMEOUT):
            self.cmd(55, 0, 0)
            r = self.cmd(41, 0x40000000, 0)
            if r == 0:
                ocr = bytearray(4)
                self.cmd(58, 0, 0, 4)
                self._sdhc = bool(ocr[0] & 0x40)
                return
            utime.sleep_ms(10)
        raise OSError("SD v2 : timeout ACMD41")

    def cmd(self, cmd, arg, crc, final=0, release=True, skip1=False):
        self.cs(0)
        self.cmdbuf[0] = 0x40 | cmd
        self.cmdbuf[1] = arg >> 24
        self.cmdbuf[2] = arg >> 16
        self.cmdbuf[3] = arg >> 8
        self.cmdbuf[4] = arg
        self.cmdbuf[5] = crc
        self.spi.write(self.cmdbuf)

        if skip1:
            self.spi.read(1, 0xFF)

        for _ in range(_CMD_TIMEOUT):
            r = self.spi.read(1, 0xFF)[0]
            if not (r & 0x80):
                break
        else:
            r = -1

        if final > 0:
            buf = bytearray(final)
            self.spi.readinto(buf, 0xFF)
            if release:
                self.cs(1)
                self.spi.write(b'\xff')
            return buf

        if release:
            self.cs(1)
            self.spi.write(b'\xff')
        return r

    def _parse_csd(self, csd):
        if (csd[0] >> 6) == 1:
            n = ((csd[9] | csd[8] << 8 | (csd[7] & 0x3F) << 16) + 1)
            return n << 10
        else:
            c = csd[6] & 3 | csd[5] << 2 | (csd[4] & 3) << 10
            e = (csd[5] >> 7) | (csd[4] & 3) << 1
            return (c + 1) * (512 << e) // 512

    def _read_sector(self, block, buf):
        if not self._sdhc:
            block <<= 9
        self.cs(0)
        if self.cmd(17, block, 0, release=False) != 0:
            self.cs(1)
            raise OSError("SD : échec CMD17")
        for _ in range(_CMD_TIMEOUT):
            token = self.spi.read(1, 0xFF)[0]
            if token == _TOKEN_DATA:
                break
        else:
            self.cs(1)
            raise OSError("SD : timeout token lecture")
        self.spi.readinto(buf)
        self.spi.read(2, 0xFF)
        self.cs(1)
        self.spi.write(b'\xff')

    def _write_sector(self, block, buf):
        if not self._sdhc:
            block <<= 9
        self.cs(0)
        if self.cmd(24, block, 0, release=False) != 0:
            self.cs(1)
            raise OSError("SD : échec CMD24")
        self.spi.write(bytes([_TOKEN_DATA]))
        self.spi.write(buf)
        self.spi.write(b'\xFF\xFF')
        r = self.spi.read(1, 0xFF)[0] & 0x1F
        if r != 0x05:
            self.cs(1)
            raise OSError(f"SD : erreur écriture token=0x{r:02X}")
        for _ in range(_CMD_TIMEOUT * 10):
            if self.spi.read(1, 0xFF)[0] != 0:
                break
            utime.sleep_ms(1)
        self.cs(1)
        self.spi.write(b'\xff')

    def readblocks(self, block_num, buf):
        for i in range(len(buf) // 512):
            self._read_sector(block_num + i, memoryview(buf)[i * 512:(i + 1) * 512])

    def writeblocks(self, block_num, buf):
        for i in range(len(buf) // 512):
            self._write_sector(block_num + i, memoryview(buf)[i * 512:(i + 1) * 512])

    def ioctl(self, op, arg):
        if op == 4:
            return self.sectors
        if op == 5:
            return 512
