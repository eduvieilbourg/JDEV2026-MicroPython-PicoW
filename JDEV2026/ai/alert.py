# =============================================================================
#  ai/alert.py — Gestionnaire d'alertes avec anti-rebond (cooldown)
# =============================================================================

import utime


class AlertManager:
    def __init__(self, cooldown_s=30):
        self._cooldown = cooldown_s
        self._last_fire = {}
        self._history = []
        self._max_history = 20

    def fire(self, alert_type, message=""):
        now = utime.time()
        last = self._last_fire.get(alert_type, 0)

        if now - last < self._cooldown:
            return False

        self._last_fire[alert_type] = now
        entry = (now, alert_type, message)
        self._history.append(entry)
        if len(self._history) > self._max_history:
            self._history.pop(0)
        return True

    def cooldown_remaining(self, alert_type):
        now = utime.time()
        last = self._last_fire.get(alert_type, 0)
        remaining = self._cooldown - (now - last)
        return max(0, remaining)

    def is_in_cooldown(self, alert_type):
        return self.cooldown_remaining(alert_type) > 0

    def get_history(self, n=10):
        recent = self._history[-n:]
        return [{"ts": ts, "type": t, "msg": m} for ts, t, m in recent]

    def count(self):
        return len(self._history)

    def reset(self):
        self._last_fire.clear()
        self._history.clear()
