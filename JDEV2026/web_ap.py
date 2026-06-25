# JDEV2026 — MicroPython sur Pico W
# Auteur : Eric Duvieilbourg — CNRS / LEMAR
# Usage pédagogique JDEV2026 : voir LICENSE_CODE_JDEV2026.md
# =============================================================================
#  web_ap.py — Serveur web embarqué en mode Point d'Accès (AP_IF)
#  Routes :
#    GET /          → dashboard HTML (static/index.html ou index_demo.html)
#    GET /data      → JSON mesure courante + état IA + type de capteur détecté
#    GET /alerts    → JSON historique des alertes
#    GET /history   → JSON dernières N mesures (depuis le CSV)
#    GET /config    → JSON configuration active (lecture seule)
#    GET /reset     → remet à zéro les stats IA
#    GET /flush     → force l'écriture du buffer CSV
# =============================================================================

import network
import socket
import utime
import ujson
import config


# ─── Streaming HTML depuis la flash (sans chargement en RAM) ──────────────────
def _send_html_file(cl, demo_mode=False):
    import os as _os
    name = "index_demo.html" if demo_mode else "index.html"
    filename = f"/{config.PROJECT_DIR}/static/{name}"

    try:
        size = _os.stat(filename)[6]
    except OSError:
        print(f"[WEB] {filename} introuvable — fallback minimal")
        _send_fallback(cl)
        return False

    header = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/html; charset=UTF-8\r\n"
        "Connection: close\r\n"
        f"Content-Length: {size}\r\n"
        "\r\n"
    )
    cl.send(header.encode("utf-8"))

    buf = bytearray(512)
    try:
        with open(filename, "rb") as f:
            while True:
                n = f.readinto(buf)
                if not n:
                    break
                cl.send(buf[:n])
    except OSError as e:
        print(f"[WEB] ERREUR streaming : {e}")
        return False

    if config.DEBUG:
        print(f"[WEB] Servi : {filename} ({size} octets)")
    return True


def _send_fallback(cl):
    body = (
        b"<!DOCTYPE html><html><head><meta charset='UTF-8'>"
        b"<meta name='viewport' content='width=device-width,initial-scale=1'>"
        b"<title>Pico W JDEV</title>"
        b"<style>body{background:#0d1117;color:#f0f6fc;font-family:monospace;padding:20px}"
        b"h1{color:#00c896}.val{font-size:2rem;font-weight:700}</style></head>"
        b"<body><h1>Pico W JDEV2026</h1>"
        b"<p>Temperature : <span id='t' class='val'>--</span> C</p>"
        b"<p>Humidite : <span id='h' class='val'>--</span> %</p>"
        b"<p style='color:#ef4444'>Fichier static/index.html manquant sur le Pico</p>"
        b"<script>setInterval(async()=>{try{const d=await(await fetch('/data')).json();"
        b"document.getElementById('t').textContent=d.temp.toFixed(1);"
        b"document.getElementById('h').textContent=d.hum.toFixed(0);}catch(e){}},2000);"
        b"</script></body></html>"
    )
    cl.send(
        f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n"
        f"Connection: close\r\nContent-Length: {len(body)}\r\n\r\n".encode()
    )
    cl.send(body)


# ─── Configuration du point d'accès WiFi ─────────────────────────────────────
def setup_ap():
    try:
        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(
            essid=config.WIFI_SSID,
            password=config.WIFI_PASSWORD,
            channel=config.WIFI_CHANNEL,
        )
        ap.ifconfig((
            config.WIFI_IP, config.WIFI_SUBNET,
            config.WIFI_GATEWAY, config.WIFI_DNS,
        ))

        timeout = 10
        while not ap.active() and timeout > 0:
            utime.sleep_ms(200)
            timeout -= 1

        if ap.active():
            ip, _, _, _ = ap.ifconfig()
            print(f"[WEB] AP actif : SSID='{config.WIFI_SSID}' "
                  f"IP={ip} Canal={config.WIFI_CHANNEL}")
            return ap
        else:
            print("[WEB] ERREUR : AP non démarré")
            return None

    except Exception as e:
        print(f"[WEB] ERREUR setup AP : {e}")
        return None


# ─── Réponses JSON ────────────────────────────────────────────────────────────
def _response_200_json(cl, data):
    body = ujson.dumps(data)
    cl.send(
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: application/json\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Connection: close\r\n"
        f"Content-Length: {len(body)}\r\n"
        "\r\n"
        + body
    )


def _response_404(cl):
    body = '{"error":"not found"}'
    cl.send(
        "HTTP/1.1 404 Not Found\r\n"
        "Content-Type: application/json\r\n"
        "Connection: close\r\n"
        f"Content-Length: {len(body)}\r\n"
        "\r\n"
        + body
    )


# ─── Payload /data ────────────────────────────────────────────────────────────
def _build_data_json(shared_data, ai_state, storage_stats):
    ai  = ai_state or {}
    sto = storage_stats or {}
    return {
        "temp": shared_data.get("temp", 0.0),
        "hum": shared_data.get("hum", 0.0),
        "ts": shared_data.get("ts", 0),
        "valid": shared_data.get("valid", False),
        "count": shared_data.get("count", 0),
        "sensor_type": shared_data.get("sensor_type", "none"),
        "simulated": shared_data.get("simulated", False),
        "anomaly": ai.get("anomaly", False),
        "zscore": ai.get("zscore", 0.0),
        "trend_label": ai.get("trend_label", "stable"),
        "slope": ai.get("trend", 0.0),
        "mean": ai.get("mean", 0.0),
        "std": ai.get("std", 0.0),
        "win_min": ai.get("min"),
        "win_max": ai.get("max"),
        "g_min": ai.get("min"),
        "g_max": ai.get("max"),
        "alert_count": ai.get("alert_count", 0),
        "storage": sto.get("mode", "?"),
        "log_lines": sto.get("lines", 0),
    }


# ─── Tâche asyncio — serveur web ─────────────────────────────────────────────
async def task_web(shared_data, ai_engine, storage_get_stats,
                   storage_get_last_n, storage_flush, demo_mode=False):
    import uasyncio as asyncio

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("", config.HTTP_PORT))
    s.listen(2)
    s.setblocking(False)

    print(f"[WEB] Serveur HTTP démarré sur port {config.HTTP_PORT} "
          f"({'DEMO' if demo_mode else 'PROD'})")

    while True:
        try:
            cl, addr = s.accept()
            cl.settimeout(3.0)
            try:
                req = cl.recv(512).decode("utf-8", "ignore")
            except OSError:
                cl.close()
                await asyncio.sleep_ms(10)
                continue

            route = "/"
            if req:
                first_line = req.split("\r\n")[0]
                parts = first_line.split(" ")
                if len(parts) >= 2:
                    route = parts[1].split("?")[0]

            if config.DEBUG:
                print(f"[WEB] {addr[0]} → {route}")

            if route == "/" or route == "/index.html":
                _send_html_file(cl, demo_mode=demo_mode)

            elif route == "/data":
                payload = _build_data_json(
                    shared_data,
                    ai_engine.state if ai_engine else None,
                    storage_get_stats() if storage_get_stats else {}
                )
                _response_200_json(cl, payload)

            elif route == "/alerts":
                alerts = []
                if ai_engine:
                    alerts = ai_engine.alerts.get_history(20)
                _response_200_json(cl, {"alerts": alerts})

            elif route == "/history":
                data = storage_get_last_n(config.GRAPH_MAX_POINTS) \
                       if storage_get_last_n else []
                _response_200_json(cl, {"history": data})

            elif route == "/config":
                cfg = {
                    "ssid": config.WIFI_SSID, "ip": config.WIFI_IP,
                    "sample_hz": config.SAMPLE_RATE_HZ,
                    "ai_window": config.AI_WINDOW_SIZE,
                    "ai_thresh": config.AI_ZSCORE_THRESH,
                    "demo_mode": demo_mode,
                    "sensor_type": shared_data.get("sensor_type", "none"),
                    "storage": storage_get_stats() if storage_get_stats else {},
                    "device": config.DEVICE_NAME,
                }
                _response_200_json(cl, cfg)

            elif route == "/reset":
                if ai_engine:
                    ai_engine.reset()
                _response_200_json(cl, {"status": "ok", "msg": "IA reinitialisee"})

            elif route == "/flush":
                if storage_flush:
                    storage_flush()
                _response_200_json(cl, {"status": "ok"})

            else:
                _response_404(cl)

        except OSError:
            pass
        except Exception as e:
            if config.DEBUG:
                print(f"[WEB] ERREUR requete : {e}")
        finally:
            try:
                cl.close()
            except Exception:
                pass

        await asyncio.sleep_ms(config.TASK_WEB_MS or 10)


# ─── Lancement direct (test autonome sur PC ou Pico) ─────────────────────────
if __name__ == "__main__":
    import uasyncio as asyncio

    config.WEB_DEMO_MODE = True
    print("[WEB] Lance en mode autonome -> WEB_DEMO_MODE force a True")
    print(f"[WEB] Dashboard : http://{config.WIFI_IP}/")
    print("[WEB] Les donnees sont simulees en JS (aucun capteur requis)")
    print()

    _demo_shared = {
        "temp": 22.0, "hum": 58.0, "ts": 0, "valid": False,
        "error": "mode demo", "count": 0, "sensor_type": "demo",
    }

    class _DemoAI:
        state = {
            "anomaly": False, "zscore": 0.0, "trend": 0.0,
            "trend_label": "stable", "mean": 22.0, "std": 0.0,
            "min": None, "max": None, "alert_count": 0, "last_alert": None,
        }
        class alerts:
            @staticmethod
            def get_history(n=10): return []
        def reset(self): pass

    async def _demo_main():
        ap = setup_ap()
        if ap:
            await task_web(
                shared_data=_demo_shared, ai_engine=_DemoAI(),
                storage_get_stats=lambda: {"mode": "demo", "lines": 0, "ready": False},
                storage_get_last_n=lambda n=60: [],
                storage_flush=lambda: None, demo_mode=True,
            )
        else:
            print("[WEB] Impossible de demarrer le point d'acces WiFi")

    asyncio.run(_demo_main())

