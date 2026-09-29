"""
In-Memory Real-Time Latency and Performance Metrics Tracker.
"""

from collections import deque
import threading
from typing import Any, Dict, List, Optional
import numpy as np

from ml.inference.models import LatencyBreakdown


class InferenceLatencyTracker:
    """
    Thread-safe tracker for edge inference latency percentiles and performance indicators.
    """

    def __init__(self, max_samples: int = 1000):
        self.max_samples = max_samples
        self._feature_gen_times: deque = deque(maxlen=max_samples)
        self._anomaly_times: deque = deque(maxlen=max_samples)
        self._rul_times: deque = deque(maxlen=max_samples)
        self._total_times: deque = deque(maxlen=max_samples)
        self._lock = threading.Lock()
        self._total_inferences: int = 0
        self._successful_inferences: int = 0
        self._failed_inferences: int = 0

    def record(
        self,
        breakdown: LatencyBreakdown,
        success: bool = True,
    ) -> None:
        """Records latency measurements for a completed inference pass."""
        with self._lock:
            self._total_inferences += 1
            if success:
                self._successful_inferences += 1
                self._feature_gen_times.append(breakdown.feature_generation_ms)
                self._anomaly_times.append(breakdown.anomaly_inference_ms)
                self._rul_times.append(breakdown.rul_inference_ms)
                self._total_times.append(breakdown.total_inference_ms)
            else:
                self._failed_inferences += 1

    def _calc_stats(self, values: deque) -> Dict[str, float]:
        if not values:
            return {"count": 0, "mean": 0.0, "median": 0.0, "p95": 0.0, "max": 0.0}

        arr = np.array(list(values), dtype=np.float64)
        return {
            "count": len(arr),
            "mean": round(float(np.mean(arr)), 3),
            "median": round(float(np.median(arr)), 3),
            "p95": round(float(np.percentile(arr, 95)), 3),
            "max": round(float(np.max(arr)), 3),
        }

    def get_summary(self) -> Dict[str, Any]:
        """Returns comprehensive latency and throughput summary."""
        with self._lock:
            return {
                "total_inferences": self._total_inferences,
                "successful_inferences": self._successful_inferences,
                "failed_inferences": self._failed_inferences,
                "success_rate_pct": round(
                    (self._successful_inferences / self._total_inferences * 100.0)
                    if self._total_inferences > 0 else 100.0,
                    2,
                ),
                "feature_generation_ms": self._calc_stats(self._feature_gen_times),
                "anomaly_inference_ms": self._calc_stats(self._anomaly_times),
                "rul_inference_ms": self._calc_stats(self._rul_times),
                "total_inference_ms": self._calc_stats(self._total_times),
            }

    def reset(self) -> None:
        """Resets all metrics counters."""
        with self._lock:
            self._feature_gen_times.clear()
            self._anomaly_times.clear()
            self._rul_times.clear()
            self._total_times.clear()
            self._total_inferences = 0
            self._successful_inferences = 0
            self._failed_inferences = 0
