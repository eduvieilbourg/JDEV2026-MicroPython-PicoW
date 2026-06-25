# JDEV2026 — MicroPython sur Pico W
# Auteur : Eric Duvieilbourg — CNRS / LEMAR
# Usage pédagogique JDEV2026 : voir LICENSE_CODE_JDEV2026.md

from machine import I2C, Pin
import utime

# Maker Pi Pico + M5Stack ENV III : GP0=SDA, GP1=SCL
# Pico Bricks I2C récent + SHTC3 : changez en GP4/GP5 si besoin
SDA_PIN = 4  # 0
SCL_PIN = 5  # 1

i2c = I2C(0, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN))

print("\n=== Étape 1 — scan I2C ===")
print(f"Bus I2C0 : SDA=GP{SDA_PIN}, SCL=GP{SCL_PIN}")

devices = i2c.scan()
print("Adresses détectées :", [hex(d) for d in devices])

if 0x44 in devices or 0x45 in devices:
    print("✓ SHT30 détecté")
elif 0x70 in devices:
    print("✓ SHTC3 détecté")
elif not devices:
    print("⚠ Aucun périphérique I2C — vérifier Grove/câblage/pins")
