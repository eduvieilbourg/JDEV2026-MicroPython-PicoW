# =============================================================================
#  ai/detector.py — Détection d'anomalie par z-score glissant
# =============================================================================

import math


class AnomalyDetector:
    def __init__(self, window=20, threshold=2.5, min_samples=5):
        self._window = []
        self._maxsize = window
        self._threshold = threshold
        self._min = min_samples
        self._n_total = 0

    def push(self, value):
        self._window.append(value)
        if len(self._window) > self._maxsize:
            self._window.pop(0)
        self._n_total += 1

        if len(self._window) < self._min:
            return False, 0.0

        mean, std = self._stats()
        if std == 0.0:
            return False, 0.0

        zscore = abs(value - mean) / std
        return zscore > self._threshold, zscore

    def _stats(self):
        n = len(self._window)
        mean = sum(self._window) / n
        variance = sum((x - mean) ** 2 for x in self._window) / n
        return mean, math.sqrt(variance)

    def get_stats(self):
        if len(self._window) < 2:
            return 0.0, 0.0
        return self._stats()

    def zscore(self, value):
        if len(self._window) < self._min:
            return 0.0
        mean, std = self._stats()
        if std == 0.0:
            return 0.0
        return abs(value - mean) / std

    def window_size(self):
        return len(self._window)

    def is_ready(self):
        return len(self._window) >= self._min

    def reset(self):
        self._window.clear()
        self._n_total = 0

    def __repr__(self):
        mean, std = self._stats() if self.is_ready() else (0.0, 0.0)
        return (f"AnomalyDetector(n={len(self._window)}/{self._maxsize}, "
                f"µ={mean:.2f}, σ={std:.3f}, thr={self._threshold})")
