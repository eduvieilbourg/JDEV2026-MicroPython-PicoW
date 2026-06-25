# JDEV2026 — MicroPython sur Pico W
# Auteur : Eric Duvieilbourg — CNRS / LEMAR
# Usage pédagogique JDEV2026 : voir LICENSE_CODE_JDEV2026.md

import math

class RollingZScore:
    def __init__(self, window=20, threshold=2.5, min_samples=8):
        self.window = window
        self.threshold = threshold
        self.min_samples = min_samples
        self.buf = []
        self.last_z = 0.0
        self.mean = 0.0
        self.std = 0.0

    def push(self, value):
        self.buf.append(value)
        if len(self.buf) > self.window:
            self.buf.pop(0)

        self.mean = sum(self.buf) / len(self.buf)
        var = sum((x - self.mean) ** 2 for x in self.buf) / len(self.buf)
        self.std = math.sqrt(var)

        if len(self.buf) < self.min_samples or self.std == 0:
            self.last_z = 0.0
            return False

        self.last_z = abs(value - self.mean) / self.std
        return self.last_z >= self.threshold
