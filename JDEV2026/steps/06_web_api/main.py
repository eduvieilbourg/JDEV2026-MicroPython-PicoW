# JDEV2026 — MicroPython sur Pico W — Étape 5 : Serveur web WiFi AP
# Auteur : Eric Duvieilbourg — CNRS / LEMAR
# Licence : CC BY-ND 4.0

import sys
sys.path.append('/JDEV2026')
sys.path.append('/JDEV2026/lib')
sys.path.append('/JDEV2026/steps/03_code_structure')

from machine import Pin
import network
import socket
import utime
import ujson
import uasyncio as asyncio

from module_acquisition import init_sensor, read_sensor


SSID     = 'ed' + 'PicoW-JDEV'
PASSWORD = 'micropython'
IP       = '192.168.4.1'

led    = Pin('LED', Pin.OUT)
sensor = init_sensor()

last = {
    'temp': 0.0,
    'hum': 0.0,
    'count': 0,
    'ts': 0,
}


HTML = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pico W JDEV2026</title>
</head>
<body style="font-family:system-ui;background:#0f172a;color:#f0f6fc;padding:24px">
<h1 style="color:#00c896">Pico W JDEV2026</h1>

<p style="font-size:52px;margin:8px 0">
  <span id="t">--</span>
  <span style="font-size:24px">°C</span>
</p>

<p style="font-size:24px">
  Humidité : <span id="h">--</span> %
</p>

<p style="color:#8b949e">
  Mesures : <span id="c">--</span>
</p>

<script>
async function updateData() {
  try {
    const r = await fetch('/data');
    const d = await r.json();

    document.getElementById('t').textContent = d.temp.toFixed(1);
    document.getElementById('h').textContent = d.hum.toFixed(0);
    document.getElementById('c').textContent = d.count;
  } catch (e) {
    console.log("Erreur fetch /data", e);
  }
}

setInterval(updateData, 1000);
updateData();
</script>

</body>
</html>
"""


def setup_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)

    ap.config(
        essid=SSID,
        password=PASSWORD
    )

    ap.ifconfig((IP, '255.255.255.0', IP, IP))

    while not ap.active():
        utime.sleep_ms(100)

    print()
    print("WiFi AP actif")
    print("SSID :", SSID)
    print("Mot de passe :", PASSWORD)
    print("Adresse :", ap.ifconfig()[0])
    print("URL : http://" + IP)


def make_response(body, content_type="text/html"):
    if isinstance(body, str):
        body = body.encode("utf-8")

    header = (
        "HTTP/1.1 200 OK\r\n"
        f"Content-Type: {content_type}; charset=utf-8\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).encode("utf-8")

    return header + body


def send_all(cl, data):
    while data:
        sent = cl.send(data)
        data = data[sent:]


async def task_acquisition():
    while True:
        temp, hum = read_sensor(sensor)

        last.update(
            temp=temp,
            hum=hum,
            count=last['count'] + 1,
            ts=utime.time()
        )

        await asyncio.sleep(1)


async def task_blink():
    while True:
        led.toggle()
        await asyncio.sleep_ms(500)


async def task_web():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("", 80))
    s.listen(2)
    s.setblocking(False)

    print("Serveur web prêt")

    while True:
        cl = None

        try:
            cl, addr = s.accept()

        except OSError:
            await asyncio.sleep_ms(20)
            continue

        try:
            cl.setblocking(True)

            req = cl.recv(1024)

            if not req:
                continue

            first_line = req.split(b"\r\n", 1)[0]
            print("HTTP :", first_line)

            if b"GET /data" in req:
                body = ujson.dumps({
                    "temp":  last["temp"],
                    "hum":   last["hum"],
                    "count": last["count"],
                    "ts":    last["ts"],
                })
                response = make_response(body, "application/json")

            elif b"GET /temp" in req:
                body = ujson.dumps({
                    "temp": last["temp"],
                    "unit": "C"
                })
                response = make_response(body, "application/json")

            else:
                response = make_response(HTML, "text/html")

            send_all(cl, response)

        except Exception as e:
            print("Erreur web :", e)

            try:
                response = make_response(
                    "Erreur serveur Pico W",
                    "text/plain"
                )
                send_all(cl, response)
            except Exception:
                pass

        finally:
            if cl:
                try:
                    cl.close()
                except Exception:
                    pass

        await asyncio.sleep_ms(0)


async def main():
    print("\n=== Étape 5 — WiFi AP + API REST ===")
    setup_ap()

    await asyncio.gather(
        task_blink(),
        task_acquisition(),
        task_web()
    )


try:
    asyncio.run(main())

except KeyboardInterrupt:
    print("\nArrêt demandé par l'utilisateur")