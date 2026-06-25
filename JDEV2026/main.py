# JDEV2026 — MicroPython sur Pico W
# Auteur : Eric Duvieilbourg — CNRS / LEMAR
# Usage pédagogique JDEV2026 : voir LICENSE_CODE_JDEV2026.md
# =============================================================================
#  main.py — Orchestrateur principal JDEV2026
#  Compatible AUTOMATIQUEMENT avec :
#    - Maker Pi Pico  + SHT30 (M5Stack ENV III)
#    - Pico Bricks    + SHTC3 (I2C, version ≥ juillet 2024)
#    - Pico Bricks    + DHT11 (1-fil, version < juillet 2024)
#    - Aucun capteur  → mode simulation automatique
#  Aucune configuration manuelle requise : la détection est automatique.
#
#  ───────────────────────────────────────────────────────────────────────
#  ⚠ NOM DU DOSSIER — À MODIFIER ICI **ET** DANS config.py SI RENOMMÉ
#  ───────────────────────────────────────────────────────────────────────
#  Ce projet est conçu pour être copié sur le Pico dans un SOUS-DOSSIER
#  (et non à la racine), afin de ne jamais écraser le main.py / picobricks.py
#  / resources.py déjà présents sur les Pico Bricks fournis par le kit.
#
#  Cette valeur DOIT être identique à PROJECT_DIR dans config.py.
#  Raison technique : ce fichier doit connaître le nom du dossier AVANT de
#  pouvoir importer config.py (c'est justement sys.path qui permet de le
#  trouver). Une vérification automatique ci-dessous bloque le démarrage
#  si les deux valeurs divergent — vous ne pouvez pas oublier l'une des deux.
# =============================================================================
PROJECT_DIR = "JDEV2026"
# =============================================================================

import sys

_project_path = "/" + PROJECT_DIR
if _project_path not in sys.path:
    sys.path.append(_project_path)

# Vérification immédiate — message clair si le dossier est introuvable,
# plutôt qu'une cascade d'ImportError difficiles à diagnostiquer.
try:
    import os
    os.stat(_project_path)
except OSError:
    print(f"\n[ERREUR] Le dossier '{_project_path}' est introuvable sur le Pico.")
    print(f"         Vérifiez le nom exact dans le panneau Fichiers de Thonny,")
    print(f"         puis corrigez PROJECT_DIR en haut de main.py si besoin.\n")
    raise SystemExit

import utime
import uasyncio as asyncio
import gc

import config

# Vérification de cohérence — empêche un renommage à moitié fait de
# provoquer un bug silencieux (ex: dashboard qui ne trouve plus static/).
if config.PROJECT_DIR != PROJECT_DIR:
    print(f"\n[ERREUR] Incohérence de nom de dossier :")
    print(f"         main.py        → PROJECT_DIR = '{PROJECT_DIR}'")
    print(f"         config.py      → PROJECT_DIR = '{config.PROJECT_DIR}'")
    print(f"         Corrigez les DEUX valeurs pour qu'elles soient identiques.\n")
    raise SystemExit


def _print_banner():
    print()
    print("=" * 50)
    print("  Pico W JDEV2026 — MicroPython Datalogger")
    print(f"  Fréquence     : {config.SAMPLE_RATE_HZ} Hz")
    print(f"  WiFi SSID     : {config.WIFI_SSID}")
    print(f"  IP            : {config.WIFI_IP}")
    print(f"  Fenêtre IA    : {config.AI_WINDOW_SIZE} mesures")
    print(f"  Seuil anomalie: {config.AI_ZSCORE_THRESH} σ")
    print("=" * 50)
    print()


async def task_watchdog():
    while True:
        await asyncio.sleep(30)
        gc.collect()
        free = gc.mem_free()
        alloc = gc.mem_alloc()
        if config.DEBUG:
            print(f"[SYS] RAM libre={free}B  alloué={alloc}B")


async def task_log_bridge(shared_data, ai_engine):
    """Bridge : à chaque mesure valide, logue dans le CSV avec métadonnées IA."""
    try:
        from storage_sdcard import log_measurement
    except Exception as e:
        print(f"[MAIN] task_log_bridge désactivée : {e}")
        return

    last_count = 0

    while True:
        await asyncio.sleep_ms(config.TASK_SENSOR_MS)

        if not shared_data.get("valid"):
            continue

        count = shared_data.get("count", 0)
        if count == last_count:
            continue
        last_count = count

        ai = ai_engine.state if ai_engine else {}
        log_measurement(
            ts=shared_data["ts"], temp=shared_data["temp"], hum=shared_data["hum"],
            sensor_type=shared_data.get("sensor_type", "?"),
            anomaly=ai.get("anomaly", False),
            trend=ai.get("trend", 0.0), zscore=ai.get("zscore", 0.0),
        )


async def main():
    _print_banner()

    # ── 1. LED de démarrage ───────────────────────────────────────────────
    from led_status import startup_sequence, task_led
    startup_sequence()

    # ── 2. Capteur — AUTO-DÉTECTION multi-matériel ────────────────────────
    from acquisition import init_sensor, task_acquisition, shared_data
    sensor_tuple = init_sensor()   # (sensor_obj, "sht30"|"shtc3"|"dht11"|"none")
    sensor_kind = sensor_tuple[1]

    if sensor_kind == "none":
        print("[MAIN] ⚠ Aucun capteur physique — mode simulation actif")
    else:
        print(f"[MAIN] ✓ Capteur actif : {sensor_kind}")

    # ── 3. Stockage ───────────────────────────────────────────────────────
    storage_ok = False
    try:
        from storage_sdcard import (init_storage, task_storage,
                                     get_stats, get_last_n, flush_buffer)
        storage_ok = init_storage()
    except Exception as e:
        print(f"[MAIN] ⚠ Module storage_sdcard indisponible : {e}")
        # Stubs de secours pour ne pas casser le reste du système
        def get_stats(): return {"mode": "unavailable", "lines": 0, "ready": False}
        def get_last_n(n=60): return []
        def flush_buffer(): pass
        async def task_storage():
            import uasyncio as asyncio
            while True:
                await asyncio.sleep(3600)

    if not storage_ok:
        print("[MAIN] ⚠ Stockage non disponible")

    # ── 4. IA ─────────────────────────────────────────────────────────────
    from ai import AIEngine, task_ai
    ai_engine = AIEngine()
    print(f"[MAIN] AIEngine initialisé")

    # ── 5. WiFi AP ────────────────────────────────────────────────────────
    from web_ap import setup_ap, task_web
    ap = setup_ap()
    if ap is None:
        print("[MAIN] ⚠ WiFi AP non disponible — serveur web désactivé")

    # ── 6. Récupération mémoire avant les tâches ─────────────────────────
    gc.collect()
    print(f"[MAIN] RAM libre avant tâches : {gc.mem_free()} octets")
    print("[MAIN] Démarrage des tâches asyncio...")
    print()

    # ── 7. Lancement des tâches ───────────────────────────────────────────
    tasks = []

    tasks.append(asyncio.create_task(task_acquisition(sensor_tuple)))
    tasks.append(asyncio.create_task(task_ai(ai_engine, shared_data)))
    tasks.append(asyncio.create_task(task_log_bridge(shared_data, ai_engine)))

    if storage_ok:
        tasks.append(asyncio.create_task(task_storage()))

    if ap is not None:
        tasks.append(asyncio.create_task(
            task_web(
                shared_data=shared_data, ai_engine=ai_engine,
                storage_get_stats=get_stats, storage_get_last_n=get_last_n,
                storage_flush=flush_buffer, demo_mode=config.WEB_DEMO_MODE,
            )
        ))
    else:
        print("[MAIN] Serveur web non démarré (pas de WiFi AP)")

    tasks.append(asyncio.create_task(task_led(shared_data, ai_engine.state)))
    tasks.append(asyncio.create_task(task_watchdog()))

    print(f"[MAIN] {len(tasks)} tâche(s) actives")
    print(f"[MAIN] Capteur          : {sensor_kind}")
    print(f"[MAIN] Connectez-vous au WiFi '{config.WIFI_SSID}'"
          f" → http://{config.WIFI_IP}")
    print()

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[MAIN] Arrêt demandé (KeyboardInterrupt)")
    except Exception as e:
        print(f"[MAIN] ERREUR fatale : {e}")
        import sys
        sys.print_exception(e)
        utime.sleep(5)
        import machine
        machine.reset()
