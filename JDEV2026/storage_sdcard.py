# JDEV2026 — MicroPython sur Pico W
# Auteur : Eric Duvieilbourg — CNRS / LEMAR
# Usage pédagogique JDEV2026 : voir LICENSE_CODE_JDEV2026.md
# =============================================================================
#  storage_sdcard.py — Stockage CSV sur carte SD (SPI) avec fallback flash
# =============================================================================

import os
import utime
import config

try:
    import lib.sdcard
    from lib.sdcard import SDCard
    from machine import SPI, Pin
    _SD_AVAILABLE = True
except (ImportError, SyntaxError, AttributeError):
    _SD_AVAILABLE = False


_storage_ready  = False
_storage_mode   = None
_log_path       = None
_write_buffer   = []
_total_written  = 0


def init_storage():
    global _storage_ready, _storage_mode, _log_path, _total_written

    if _SD_AVAILABLE:
        try:
            spi = SPI(
                config.SD_SPI_ID,
                sck=Pin(config.SD_SCK_PIN),
                mosi=Pin(config.SD_MOSI_PIN),
                miso=Pin(config.SD_MISO_PIN),
                baudrate=1_000_000
            )
            cs = Pin(config.SD_CS_PIN, Pin.OUT)
            sd = SDCard(spi, cs)
            os.mount(sd, "/sd")
            _log_path     = f"/sd/{config.LOG_FILENAME}"
            _storage_mode = "sd"
            if config.DEBUG:
                print("[STORAGE] Carte SD montée sur /sd")
        except Exception as e:
            print(f"[STORAGE] SD indisponible ({e}) — bascule sur flash")
            _sd_fallback_to_flash()
    else:
        if config.DEBUG:
            print("[STORAGE] Driver SD absent — stockage sur flash interne")
        _sd_fallback_to_flash()

    if _log_path:
        _ensure_csv_header()
        _total_written = _count_lines(_log_path)
        _storage_ready = True
        print(f"[STORAGE] Prêt ({_storage_mode}) : {_log_path} ({_total_written} lignes)")
        return True

    print("[STORAGE] ERREUR : aucun support de stockage disponible")
    return False


def _sd_fallback_to_flash():
    global _storage_mode, _log_path
    try:
        os.mkdir(config.LOG_FLASH_DIR)
    except OSError:
        pass
    _log_path     = f"{config.LOG_FLASH_DIR}/{config.LOG_FILENAME}"
    _storage_mode = "flash"


def _ensure_csv_header():
    try:
        with open(_log_path, "r") as f:
            f.read(1)
    except OSError:
        with open(_log_path, "w") as f:
            f.write("timestamp_unix,iso_time,temp_c,hum_pct,"
                    "sensor_type,anomaly,trend,zscore\n")
        if config.DEBUG:
            print(f"[STORAGE] Fichier CSV créé : {_log_path}")


def _count_lines(path):
    try:
        count = 0
        with open(path, "r") as f:
            for _ in f:
                count += 1
        return max(0, count - 1)
    except OSError:
        return 0


def _iso_time(ts):
    try:
        t = utime.gmtime(ts)
        return f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}Z"
    except Exception:
        return "0000-00-00T00:00:00Z"


def log_measurement(ts, temp, hum, sensor_type="?", anomaly=False, trend=0.0, zscore=0.0):
    global _write_buffer
    if not _storage_ready:
        return False

    _write_buffer.append((ts, temp, hum, sensor_type, anomaly, trend, zscore))

    if len(_write_buffer) >= config.LOG_BUFFER_SIZE:
        return flush_buffer()
    return True


def flush_buffer():
    global _write_buffer, _total_written

    if not _write_buffer:
        return True
    if not _storage_ready:
        return False

    if _total_written >= config.LOG_MAX_LINES:
        _rotate_log()

    try:
        with open(_log_path, "a") as f:
            for (ts, temp, hum, stype, anomaly, trend, zscore) in _write_buffer:
                iso = _iso_time(ts)
                line = (f"{ts},{iso},{temp:.2f},{hum:.1f},{stype},"
                        f"{1 if anomaly else 0},{trend:.4f},{zscore:.3f}\n")
                f.write(line)
                _total_written += 1

        written = len(_write_buffer)
        _write_buffer.clear()

        if config.DEBUG:
            print(f"[STORAGE] {written} ligne(s) écrite(s) "
                  f"(total: {_total_written}, mode: {_storage_mode})")
        return True

    except OSError as e:
        print(f"[STORAGE] ERREUR écriture : {e}")
        _write_buffer.clear()
        return False


def _rotate_log():
    global _total_written
    try:
        backup = _log_path.replace(".csv", "_old.csv")
        try:
            os.remove(backup)
        except OSError:
            pass
        os.rename(_log_path, backup)
        _ensure_csv_header()
        _total_written = 0
        if config.DEBUG:
            print(f"[STORAGE] Rotation : {_log_path} → {backup}")
    except OSError as e:
        print(f"[STORAGE] ERREUR rotation : {e}")


def get_last_n(n=60):
    if not _storage_ready:
        return []
    try:
        lines = []
        with open(_log_path, "r") as f:
            for line in f:
                lines.append(line.strip())

        data_lines = [l for l in lines[1:] if l]
        recent = data_lines[-n:] if len(data_lines) > n else data_lines

        result = []
        for line in recent:
            parts = line.split(",")
            if len(parts) >= 4:
                try:
                    result.append({
                        "ts": int(parts[0]), "iso": parts[1],
                        "temp": float(parts[2]), "hum": float(parts[3]),
                        "sensor_type": parts[4] if len(parts) > 4 else "?",
                        "anomaly": parts[5] == "1" if len(parts) > 5 else False,
                    })
                except (ValueError, IndexError):
                    pass
        return result
    except OSError:
        return []


def get_stats():
    return {
        "mode": _storage_mode, "path": _log_path,
        "lines": _total_written, "buffered": len(_write_buffer),
        "ready": _storage_ready,
    }


async def task_storage():
    import uasyncio as asyncio
    if config.DEBUG:
        print(f"[STORAGE] Tâche démarrée — flush toutes les {config.TASK_STORAGE_MS}ms")
    while True:
        await asyncio.sleep_ms(config.TASK_STORAGE_MS)
        flush_buffer()


if __name__ == "__main__":
    ok = init_storage()
    if ok:
        ts = utime.time()
        for i in range(15):
            log_measurement(ts + i, 20.0 + i * 0.1, 50.0 + i * 0.2, "test")
        flush_buffer()
        print(f"\nStats : {get_stats()}")
        print(f"5 dernières : {get_last_n(5)}")

