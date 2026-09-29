"""
Recovery Metrics Collector.
Tracks detection latency, recovery duration, buffered messages, replay throughput, and data loss counts.
"""

from datetime import datetime, timezone
import time
from typing import Dict, List, Optional
from failure_testing.models import RecoveryMetrics


class RecoveryMetricsTracker:
    """
    Measures and accumulates resilience and recovery metrics during failure testing.
    """

    def __init__(self):
        self.metrics = RecoveryMetrics()
        self._start_time: Optional[float] = None
        self._recovery_start: Optional[float] = None

    def start_measurement(self) -> None:
        self._start_time = time.perf_counter()

    def record_detection(self) -> None:
        if self._start_time:
            self.metrics.detection_latency_ms = round((time.perf_counter() - self._start_time) * 1000.0, 2)

    def start_recovery(self) -> None:
        self._recovery_start = time.perf_counter()

    def stop_recovery(self) -> None:
        if self._recovery_start:
            self.metrics.recovery_latency_ms = round((time.perf_counter() - self._recovery_start) * 1000.0, 2)

    def record_buffered(self, count: int = 1) -> None:
        self.metrics.buffered_events_count += count

    def record_replayed(self, count: int = 1) -> None:
        self.metrics.replayed_events_count += count

    def record_lost(self, count: int = 1) -> None:
        self.metrics.lost_events_count += count

    def record_duplicate(self, count: int = 1) -> None:
        self.metrics.duplicate_persisted_count += count

    def record_job_retry(self, count: int = 1) -> None:
        self.metrics.job_retries_count += count

    def get_metrics(self) -> RecoveryMetrics:
        return self.metrics
