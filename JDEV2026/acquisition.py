# JDEV2026 — MicroPython sur Pico W
# Auteur : Eric Duvieilbourg — CNRS / LEMAR
# Usage pédagogique JDEV2026 : voir LICENSE_CODE_JDEV2026.md
# =============================================================================
#  acquisition.py — Acquisition capteur avec AUTO-DÉTECTION multi-matériel
#
#  Supporte automatiquement, sans aucune configuration manuelle :
#    1. SHT30  (I2C 0x44/0x45)  — Maker Pi Pico + M5Stack ENV III
#    2. SHTC3  (I2C 0x70)       — Pico Bricks version ≥ juillet 2024
#    3. DHT11  (1-fil, GP11)    — Pico Bricks version < juillet 2024
#    4. Aucun capteur détecté   — mode simulation automatique
#
#  shared_data["sensor_type"] indique lequel a été détecté, utilisé par le
#  dashboard web pour afficher la source réelle des données.
# =============================================================================

import utime
import math
from machine import I2C, Pin
import config


# ─── Buffer partagé (accédé par toutes les tâches) ───────────────────────────
shared_data = {
    "temp":        0.0,
    "hum":         0.0,
    "ts":          0,
    "valid":       False,
    "error":       None,
    "count":       0,
    "simulated":   False,
    "sensor_type": "none",   # "sht30" | "shtc3" | "dht11" | "simulated"
}


# ─── Générateur de données simulées (fallback ultime) ────────────────────────
_sim_t0 = None

def _simulated_measure():
    """
    Génère température/humidité synthétiques — identique à la logique
    JS du dashboard de démo, pour cohérence visuelle.
    """
    global _sim_t0
    if _sim_t0 is None:
        _sim_t0 = utime.ticks_ms()

    t = utime.ticks_diff(utime.ticks_ms(), _sim_t0) / 1000.0

    seed = int(t * 1000) & 0xFFFFFFFF
    seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
    noise_t = ((seed / 0xFFFFFFFF) - 0.5) * 0.24
    seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
    noise_h = ((seed / 0xFFFFFFFF) - 0.5) * 1.0

    spike = 0.0
    if int(t) % 14 == 0 and t - int(t) < (config.TASK_SENSOR_MS / 1000.0):
        spike = 6.0 + ((seed / 0xFFFFFFFF) * 4.0)

    temp = 22.0 + 1.5 * math.sin(t / 40.0) + 0.3 * math.sin(t / 8.0) + noise_t + spike
    hum  = max(20.0, min(100.0, 58.0 - 0.4 * math.sin(t / 40.0) + noise_h))

    return round(temp, 2), round(hum, 1)


# ─── Auto-détection du capteur ────────────────────────────────────────────────
def detect_sensor():
    """
    Teste le capteur I2C, puis DHT11 (1-fil) si rien trouvé.

    ⚠ CONTRAINTE MATÉRIELLE CRITIQUE (RP2040/RP2350) — confirmée par un bug
    officiel du dépôt MicroPython (issue #13536) et reproduite en test réel :
    réinitialiser le contrôleur I2C0 sur un second jeu de broches après un
    premier essai (même raté) CASSE DÉFINITIVEMENT le bus jusqu'au prochain
    reset matériel complet — un simple soft reboot ne suffit pas à réparer.

    Conséquence : on ne doit JAMAIS créer plus d'un objet I2C(0, ...) par
    run, quel que soit le résultat du premier essai. La détection se fait
    donc sur UN SEUL jeu de broches I2C, déterminé une fois pour toutes.
    Pour supporter les deux familles de cartes, le DHT11 (qui n'utilise pas
    I2C du tout) est testé en complément, sans jamais toucher au bus I2C.
    """
    # ── Bus I2C unique — déterminé par config.BOARD_I2C_PINS, jamais les
    #    deux jeux de broches dans le même run (voir docstring ci-dessus) ──
    if config.BOARD_I2C_PINS == "maker":
        sda_pin, scl_pin, label = (
            config.I2C_SDA_PIN_MAKER, config.I2C_SCL_PIN_MAKER, "GP0/GP1"
        )
    else:
        sda_pin, scl_pin, label = (
            config.I2C_SDA_PIN_BRICKS, config.I2C_SCL_PIN_BRICKS, "GP4/GP5"
        )

    sensor, kind = _try_i2c_sensors(sda_pin=sda_pin, scl_pin=scl_pin, label=label)
    if sensor is not None:
        return sensor, kind

    # ── DHT11 1-fil (Pico Bricks ancien, GP11) — broche indépendante,
    #    n'utilise pas le contrôleur I2C, donc SANS RISQUE de casser le bus ──
    try:
        from lib.picobricks_sensors import DHT11
        pin = Pin(config.DHT11_PIN)
        dht = DHT11(pin)
        dht.measure()
        utime.sleep_ms(250)
        print(f"[ACQ] ✓ DHT11 détecté sur GP{config.DHT11_PIN}")
        return dht, "dht11"
    except Exception as e:
        if config.DEBUG:
            print(f"[ACQ]   DHT11 GP{config.DHT11_PIN} : absent ou erreur ({e})")

    print("[ACQ] ⚠ Aucun capteur détecté → MODE SIMULATION activé")
    print(f"[ACQ]   (Bus I2C testé : {label}. Si votre capteur est sur "
          f"l'autre jeu de broches, changez BOARD_I2C_PINS dans config.py)")
    return None, "none"


def _try_i2c_sensors(sda_pin, scl_pin, label):
    """
    Teste SHTC3 puis SHT30 sur UN SEUL bus I2C donné.
    Une détection n'est validée QUE si une mesure réelle réussit.

    freq volontairement NON précisé (comme le code officiel Pico Bricks
    qui fonctionne) — un freq=100_000 explicite a provoqué des OSError EIO
    systématiques en test réel, alors que l'absence de freq fonctionnait.
    """
    try:
        i2c = I2C(config.I2C_ID, sda=Pin(sda_pin), scl=Pin(scl_pin))
        devices = i2c.scan()
        if config.DEBUG:
            print(f"[ACQ] I2C scan {label} : {[hex(d) for d in devices]} "
                  f"({len(devices)} adresse(s))")

        # SHTC3 — adresse fixe 0x70 — testé en premier (matériel confirmé
        # sur Pico Bricks via le code officiel du kit)
        if config.SHTC3_ADDR in devices:
            try:
                from lib.picobricks_sensors import SHTC3
                sensor = SHTC3(i2c)
                sensor.temperature()   # ← test réel
                print(f"[ACQ] ✓ SHTC3 détecté ET validé sur {label} (0x70)")
                return sensor, "shtc3"
            except Exception as e:
                if config.DEBUG:
                    print(f"[ACQ]   0x70 présent sur {label} "
                          f"mais mesure SHTC3 échouée ({e})")
                utime.sleep_ms(50)   # laisse le bus se stabiliser avant la suite

        # SHT30 — adresse 0x44 ou 0x45 — VALIDÉ par une mesure réelle
        for addr in (config.SHT30_ADDR, 0x45 if config.SHT30_ADDR == 0x44 else 0x44):
            if addr in devices:
                try:
                    from lib.sht30 import SHT30
                    sensor = SHT30(i2c, address=addr)
                    sensor.measure()   # ← test réel, lève SHT30Error si échec
                    print(f"[ACQ] ✓ SHT30 détecté ET validé sur {label} (0x{addr:02X})")
                    return sensor, "sht30"
                except Exception as e:
                    if config.DEBUG:
                        print(f"[ACQ]   0x{addr:02X} présent sur {label} "
                              f"mais mesure SHT30 échouée ({e})")

    except Exception as e:
        if config.DEBUG:
            print(f"[ACQ]   Bus I2C {label} : indisponible ({e})")

    return None, None


# ─── Mesure unifiée (gère les 3 types de capteur + simulation) ──────────────
def read_sensor(sensor_tuple):
    """
    sensor_tuple = (sensor_object, sensor_type) retourné par detect_sensor().
    Lit le capteur quel que soit son type, normalise le résultat,
    met à jour shared_data. Retourne (temp, hum) ou (None, None) si erreur.
    """
    global shared_data
    sensor, kind = sensor_tuple

    try:
        if kind == "sht30":
            temp, hum = sensor.measure()

        elif kind == "shtc3":
            temp = sensor.temperature()
            hum  = sensor.humidity()

        elif kind == "dht11":
            sensor.measure()   # respecte son propre anti-rebond interne (200ms)
            temp = sensor.temperature
            hum  = sensor.humidity

        else:  # "none" → simulation
            temp, hum = _simulated_measure()
            shared_data["simulated"] = True

        shared_data.update({
            "temp": temp, "hum": hum, "ts": utime.time(),
            "valid": True, "error": None,
            "sensor_type": kind if kind != "none" else "simulated",
            "simulated": (kind == "none"),
        })
        shared_data["count"] += 1

        if config.LOG_TO_CONSOLE:
            tag = "~sim" if kind == "none" else kind
            print(f"[ACQ:{tag}] #{shared_data['count']:05d}  "
                  f"T={temp:.2f}°C  H={hum:.1f}%")
        return temp, hum

    except Exception as e:
        # DHT11 lève fréquemment InvalidChecksum / InvalidPulseCount —
        # on l'ignore et on retente à la prochaine période, sans planter.
        shared_data["valid"] = False
        shared_data["error"] = str(e)
        if config.DEBUG:
            print(f"[ACQ] Erreur lecture ({kind}) : {e}")
        return None, None


# ─── Initialisation (point d'entrée appelé par main.py) ──────────────────────
def init_sensor():
    """
    Détecte et initialise le capteur disponible.
    Retourne un tuple (sensor, kind) — kind="none" si simulation.
    """
    if not config.AUTO_DETECT_SENSOR:
        print("[ACQ] AUTO_DETECT_SENSOR désactivé — mode simulation forcé")
        return None, "none"
    return detect_sensor()


# ─── Tâche asyncio — acquisition périodique avec timing précis ───────────────
async def task_acquisition(sensor_tuple):
    """
    Tâche principale d'acquisition. Timing robuste via ticks_ms.
    Fonctionne identiquement quel que soit le capteur détecté.
    """
    import uasyncio as asyncio

    sensor, kind = sensor_tuple
    period_ms = config.TASK_SENSOR_MS

    # Le DHT11 ne supporte pas moins de 200ms entre mesures (contrainte
    # matérielle) — on protège contre une config trop agressive.
    if kind == "dht11" and period_ms < 250:
        print(f"[ACQ] ⚠ DHT11 limité à 200ms min — période ajustée à 250ms")
        period_ms = 250

    if config.DEBUG:
        print(f"[ACQ] Tâche démarrée — capteur={kind} — période {period_ms}ms")

    t_next = utime.ticks_ms()

    while True:
        read_sensor(sensor_tuple)

        t_next = utime.ticks_add(t_next, period_ms)
        delay  = utime.ticks_diff(t_next, utime.ticks_ms())
        if delay > 0:
            await asyncio.sleep_ms(delay)
        else:
            await asyncio.sleep_ms(0)


# ─── Test autonome ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("  Détection automatique du capteur...")
    print("=" * 50)
    sensor_tuple = init_sensor()
    print(f"\nCapteur détecté : {sensor_tuple[1]}")
    print("5 mesures :\n")
    for i in range(5):
        t, h = read_sensor(sensor_tuple)
        if t is not None:
            print(f"  {i+1}/5  T={t:.2f}°C  H={h:.1f}%")
        utime.sleep_ms(1000)
