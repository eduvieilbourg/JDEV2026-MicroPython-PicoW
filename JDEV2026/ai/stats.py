# =============================================================================
#  ai/stats.py — Statistiques descriptives sur fenêtre glissante
# =============================================================================

import math


class RollingStats:
    def __init__(self, window=20):
        self._window = []
        self._maxsize = window
        self._global_min = None
        self._global_max = None
        self._total_count = 0

    def push(self, value):
        self._window.append(value)
        if len(self._window) > self._maxsize:
            self._window.pop(0)
        self._total_count += 1

        if self._global_min is None or value < self._global_min:
            self._global_min = value
        if self._global_max is None or value > self._global_max:
            self._global_max = value

    def get(self):
        n = len(self._window)
        if n == 0:
            return 0.0, 0.0
        mean = sum(self._window) / n
        if n < 2:
            return mean, 0.0
        variance = sum((x - mean) ** 2 for x in self._window) / n
        return mean, math.sqrt(variance)

    def mean(self):
        m, _ = self.get()
        return m

    def std(self):
        _, s = self.get()
        return s

    def minimum(self):
        return min(self._window) if self._window else None

    def maximum(self):
        return max(self._window) if self._window else None

    def global_min(self):
        return self._global_min

    def global_max(self):
        return self._global_max

    def median(self):
        if not self._window:
            return None
        s = sorted(self._window)
        n = len(s)
        mid = n // 2
        if n % 2 == 0:
            return (s[mid - 1] + s[mid]) / 2.0
        return s[mid]

    def count(self):
        return self._total_count

    def window_count(self):
        return len(self._window)

    def reset(self):
        self._window.clear()
        self._global_min = None
        self._global_max = None
        self._total_count = 0

    def summary(self):
        mean, std = self.get()
        return {
            "n": self._total_count, "window": len(self._window),
            "mean": round(mean, 2), "std": round(std, 3),
            "min": self.minimum(), "max": self.maximum(),
            "g_min": self._global_min, "g_max": self._global_max,
        }
