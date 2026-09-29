"""
Windowed Anomaly Aggregator for Temporal Anomaly Detection.

Prevents per-second false positives by requiring a sustained ratio of anomalous
readings within a sliding time window before confirming an anomaly event.

Industry rationale:
  - Industrial sensors legitimately spike briefly (vibration during load change, thermal
    transient on startup). A single high anomaly score at t=N is not actionable.
  - Only when >= `alert_ratio_threshold` of the last `window_size` readings are flagged
    as anomalous is the condition considered a real, sustained deviation.
  - `min_readings_before_alert` prevents false positives during the warmup phase.
"""

import logging
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional

from ml.inference.models import AnomalyLabel
from ml.inference.result import MLInferenceResult

logger = logging.getLogger(__name__)


class MachineAnomalyWindow:
    """
    Sliding window of recent ML inference results for a single machine.
    Computes a windowed anomaly score and determines if a sustained anomaly is present.
    """

    def __init__(
        self,
        machine_id: str,
        window_size: int = 30,
        min_readings_before_alert: int = 10,
        alert_ratio_threshold: float = 0.40,
        score_ema_alpha: float = 0.2,
    ):
        self.machine_id = machine_id
        self.window_size = window_size
        self.min_readings_before_alert = min_readings_before_alert
        self.alert_ratio_threshold = alert_ratio_threshold
        self.score_ema_alpha = score_ema_alpha

        self._results: Deque[MLInferenceResult] = deque(maxlen=window_size)
        self._ema_score: Optional[float] = None  # Exponential moving average of anomaly score
        self._sustained_anomaly_count: int = 0    # Consecutive windows confirming anomaly
        self._last_alert_state: bool = False

    def add(self, result: MLInferenceResult) -> None:
        """Append a new inference result to the window."""
        self._results.append(result)

        # Update EMA score
        score = result.anomaly_score if result.anomaly_score is not None else 0.0
        if self._ema_score is None:
            self._ema_score = score
        else:
            self._ema_score = (self.score_ema_alpha * score) + ((1.0 - self.score_ema_alpha) * self._ema_score)

    @property
    def reading_count(self) -> int:
        return len(self._results)

    @property
    def ema_score(self) -> float:
        return self._ema_score or 0.0

    @property
    def anomaly_ratio(self) -> float:
        """Fraction of readings in the current window that are labeled ANOMALOUS."""
        if not self._results:
            return 0.0
        count = sum(
            1 for r in self._results
            if r.anomaly_label == AnomalyLabel.ANOMALOUS
        )
        return count / len(self._results)

    @property
    def mean_score(self) -> float:
        """Average calibrated anomaly score across the window."""
        if not self._results:
            return 0.0
        scores = [r.anomaly_score for r in self._results if r.anomaly_score is not None]
        return sum(scores) / len(scores) if scores else 0.0

    def is_sustained_anomaly(self) -> bool:
        """
        Returns True only when:
          1. Enough readings have been collected (>= min_readings_before_alert)
          2. The anomaly ratio in the window meets or exceeds the threshold
        """
        if self.reading_count < self.min_readings_before_alert:
            return False
        return self.anomaly_ratio >= self.alert_ratio_threshold

    def get_latest_result(self) -> Optional[MLInferenceResult]:
        """Returns the most recent inference result."""
        return self._results[-1] if self._results else None

    def get_window_summary(self) -> Dict[str, Any]:
        """Returns a summary dict of the current window state."""
        return {
            "machine_id": self.machine_id,
            "reading_count": self.reading_count,
            "window_size": self.window_size,
            "anomaly_ratio": round(self.anomaly_ratio, 4),
            "mean_score": round(self.mean_score, 4),
            "ema_score": round(self.ema_score, 4),
            "is_sustained_anomaly": self.is_sustained_anomaly(),
            "alert_ratio_threshold": self.alert_ratio_threshold,
        }


class WindowedAnomalyAggregator:
    """
    Fleet-wide registry of per-machine sliding anomaly windows.

    Usage in the ingestion worker:
      1. After each ML inference: aggregator.record(ml_result)
      2. Before alerting:         aggregator.should_alert(machine_id)
      3. After alert is resolved: aggregator.reset_machine(machine_id)
    """

    def __init__(
        self,
        window_size: int = 30,
        min_readings_before_alert: int = 10,
        alert_ratio_threshold: float = 0.40,
        score_ema_alpha: float = 0.2,
    ):
        self.window_size = window_size
        self.min_readings_before_alert = min_readings_before_alert
        self.alert_ratio_threshold = alert_ratio_threshold
        self.score_ema_alpha = score_ema_alpha
        self._windows: Dict[str, MachineAnomalyWindow] = {}

    def _get_or_create(self, machine_id: str) -> MachineAnomalyWindow:
        if machine_id not in self._windows:
            self._windows[machine_id] = MachineAnomalyWindow(
                machine_id=machine_id,
                window_size=self.window_size,
                min_readings_before_alert=self.min_readings_before_alert,
                alert_ratio_threshold=self.alert_ratio_threshold,
                score_ema_alpha=self.score_ema_alpha,
            )
        return self._windows[machine_id]

    def record(self, result: MLInferenceResult) -> None:
        """Record a new inference result into the appropriate machine window."""
        window = self._get_or_create(result.machine_id)
        window.add(result)

    def should_alert(self, machine_id: str) -> bool:
        """
        Returns True if the machine's sliding window confirms a sustained anomaly.
        Safe to call even if the machine has no window yet (returns False).
        """
        if machine_id not in self._windows:
            return False
        return self._windows[machine_id].is_sustained_anomaly()

    def get_window_summary(self, machine_id: str) -> Optional[Dict[str, Any]]:
        """Returns the current window summary for a machine, or None if not tracked."""
        if machine_id not in self._windows:
            return None
        return self._windows[machine_id].get_window_summary()

    def get_all_summaries(self) -> List[Dict[str, Any]]:
        """Returns summaries for all tracked machines."""
        return [w.get_window_summary() for w in self._windows.values()]

    def get_ema_score(self, machine_id: str) -> float:
        """Returns the exponential moving average anomaly score for a machine."""
        if machine_id not in self._windows:
            return 0.0
        return self._windows[machine_id].ema_score

    def get_anomaly_ratio(self, machine_id: str) -> float:
        """Returns the current anomaly ratio for a machine."""
        if machine_id not in self._windows:
            return 0.0
        return self._windows[machine_id].anomaly_ratio

    def reset_machine(self, machine_id: str) -> None:
        """Clears the sliding window for a machine (e.g., after recovery)."""
        if machine_id in self._windows:
            del self._windows[machine_id]
            logger.info(f"[AnomalyAggregator] Window reset for machine {machine_id}")

    def reset_all(self) -> None:
        """Clears all machine windows."""
        self._windows.clear()

    @property
    def tracked_machines(self) -> List[str]:
        return list(self._windows.keys())
