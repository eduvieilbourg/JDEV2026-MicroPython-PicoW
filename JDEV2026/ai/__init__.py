# =============================================================================
#  ai/__init__.py — Module IA embarquée JDEV2026
# =============================================================================

from ai.detector import AnomalyDetector
from ai.trend     import TrendAnalyzer
from ai.stats     import RollingStats
from ai.alert     import AlertManager
import config


class AIEngine:
    def __init__(self):
        self.detector = AnomalyDetector(
            window=config.AI_WINDOW_SIZE,
            threshold=config.AI_ZSCORE_THRESH,
            min_samples=config.AI_MIN_SAMPLES
        )
        self.trend  = TrendAnalyzer(window=config.AI_TREND_WINDOW)
        self.stats  = RollingStats(window=config.AI_WINDOW_SIZE)
        self.alerts = AlertManager(cooldown_s=config.AI_ALERT_COOLDOWN)

        self.state = {
            "anomaly": False, "zscore": 0.0,
            "trend": 0.0, "trend_label": "stable",
            "mean": 0.0, "std": 0.0,
            "min": None, "max": None,
            "alert_count": 0, "last_alert": None,
        }

    def update(self, temp, hum):
        self.stats.push(temp)
        mean, std = self.stats.get()

        is_anomaly, zscore = self.detector.push(temp)
        slope = self.trend.push(temp)
        trend_label = self.trend.label(slope)

        if is_anomaly:
            fired = self.alerts.fire("temp_anomaly", f"T={temp:.1f}°C z={zscore:.2f}")
            if fired:
                self.state["alert_count"] += 1
                self.state["last_alert"] = temp

        self.state.update({
            "anomaly": is_anomaly, "zscore": round(zscore, 3),
            "trend": round(slope, 4), "trend_label": trend_label,
            "mean": round(mean, 2), "std": round(std, 3),
            "min": self.stats.minimum(), "max": self.stats.maximum(),
        })

        if config.DEBUG and is_anomaly:
            print(f"[AI] ⚠ ANOMALIE  T={temp:.2f}°C  z={zscore:.2f}  "
                  f"trend={trend_label}  alertes={self.state['alert_count']}")

        return self.state

    def reset(self):
        self.detector.reset()
        self.trend.reset()
        self.stats.reset()
        self.alerts.reset()


async def task_ai(engine, shared_data):
    import uasyncio as asyncio
    if config.DEBUG:
        print(f"[AI] Tâche démarrée — fenêtre={config.AI_WINDOW_SIZE} "
              f"seuil={config.AI_ZSCORE_THRESH}σ")
    while True:
        await asyncio.sleep_ms(config.TASK_AI_MS)
        if shared_data.get("valid"):
            engine.update(shared_data["temp"], shared_data["hum"])
