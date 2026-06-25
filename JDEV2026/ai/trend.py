# =============================================================================
#  ai/trend.py — Analyse de tendance par régression linéaire glissante
# =============================================================================


class TrendAnalyzer:
    DEAD_BAND = 0.05
    RISING_FAST = 0.5
    FALLING_FAST = -0.5

    def __init__(self, window=10):
        self._window = []
        self._maxsize = window

    def push(self, value):
        self._window.append(value)
        if len(self._window) > self._maxsize:
            self._window.pop(0)
        return self._slope()

    def _slope(self):
        n = len(self._window)
        if n < 2:
            return 0.0
        sx  = n * (n - 1) / 2
        sx2 = n * (n - 1) * (2*n - 1) / 6
        sy  = sum(self._window)
        sxy = sum(i * self._window[i] for i in range(n))
        denom = n * sx2 - sx * sx
        if denom == 0:
            return 0.0
        return (n * sxy - sx * sy) / denom

    def label(self, slope=None):
        if slope is None:
            slope = self._slope()
        if slope > self.RISING_FAST:
            return "hausse rapide"
        elif slope > self.DEAD_BAND:
            return "hausse"
        elif slope < self.FALLING_FAST:
            return "chute rapide"
        elif slope < -self.DEAD_BAND:
            return "baisse"
        else:
            return "stable"

    def get(self):
        return self._slope()

    def reset(self):
        self._window.clear()
