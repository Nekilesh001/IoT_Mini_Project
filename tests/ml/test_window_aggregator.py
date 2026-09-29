"""
Tests for WindowedAnomalyAggregator — sliding window ML anomaly gating.
Covers: warmup guard, ratio threshold, EMA score, window cycling, fleet registry.
"""

from datetime import datetime, timezone

import pytest

from ml.inference.models import AnomalyLabel, InferenceStatus
from ml.inference.result import MLInferenceResult
from ml.inference.window_aggregator import MachineAnomalyWindow, WindowedAnomalyAggregator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_result(
    machine_id: str = "PMP-001",
    anomaly_score: float = 0.3,
    label: AnomalyLabel = AnomalyLabel.NORMAL,
) -> MLInferenceResult:
    return MLInferenceResult(
        machine_id=machine_id,
        machine_type="INDUSTRIAL_PUMP",
        event_time=datetime.now(timezone.utc),
        anomaly_score=anomaly_score,
        raw_anomaly_score=-0.4,
        anomaly_label=label,
        predicted_rul_seconds=3600.0,
        status=InferenceStatus.READY,
    )


# ---------------------------------------------------------------------------
# MachineAnomalyWindow tests
# ---------------------------------------------------------------------------

class TestMachineAnomalyWindow:

    def test_no_alert_before_warmup(self):
        """Should never alert until min_readings_before_alert is reached."""
        window = MachineAnomalyWindow(
            machine_id="CNC-001",
            window_size=30,
            min_readings_before_alert=10,
            alert_ratio_threshold=0.40,
        )
        # Feed 9 fully anomalous readings — still below warmup
        for _ in range(9):
            window.add(make_result("CNC-001", 0.9, AnomalyLabel.ANOMALOUS))

        assert window.reading_count == 9
        assert not window.is_sustained_anomaly(), "Must not alert before warmup"

    def test_alert_fires_after_warmup_and_threshold(self):
        """Alert should fire once warmup is reached and 40%+ are anomalous."""
        window = MachineAnomalyWindow(
            machine_id="CNC-001",
            window_size=30,
            min_readings_before_alert=10,
            alert_ratio_threshold=0.40,
        )
        # 6 anomalous + 4 normal = 60% anomaly ratio → should alert
        for _ in range(6):
            window.add(make_result("CNC-001", 0.9, AnomalyLabel.ANOMALOUS))
        for _ in range(4):
            window.add(make_result("CNC-001", 0.1, AnomalyLabel.NORMAL))

        assert window.reading_count == 10
        assert window.anomaly_ratio == pytest.approx(0.6)
        assert window.is_sustained_anomaly()

    def test_no_alert_below_ratio_threshold(self):
        """10 readings but only 30% anomalous — below 40% threshold, no alert."""
        window = MachineAnomalyWindow(
            machine_id="CNC-001",
            window_size=30,
            min_readings_before_alert=10,
            alert_ratio_threshold=0.40,
        )
        for _ in range(3):
            window.add(make_result("CNC-001", 0.9, AnomalyLabel.ANOMALOUS))
        for _ in range(7):
            window.add(make_result("CNC-001", 0.1, AnomalyLabel.NORMAL))

        assert window.reading_count == 10
        assert window.anomaly_ratio == pytest.approx(0.3)
        assert not window.is_sustained_anomaly()

    def test_window_slides_correctly(self):
        """Old readings fall off when window is full; ratio updates correctly."""
        window = MachineAnomalyWindow(
            machine_id="CNC-001",
            window_size=5,
            min_readings_before_alert=5,
            alert_ratio_threshold=0.40,
        )
        # Fill with 5 anomalous readings
        for _ in range(5):
            window.add(make_result("CNC-001", 0.9, AnomalyLabel.ANOMALOUS))
        assert window.is_sustained_anomaly()

        # Add 5 normal readings — old anomalous ones slide out
        for _ in range(5):
            window.add(make_result("CNC-001", 0.1, AnomalyLabel.NORMAL))

        assert window.anomaly_ratio == pytest.approx(0.0)
        assert not window.is_sustained_anomaly()

    def test_ema_score_converges(self):
        """EMA should converge towards the constant score being fed in."""
        window = MachineAnomalyWindow(machine_id="M-001", score_ema_alpha=0.5)
        for _ in range(20):
            window.add(make_result("M-001", 0.8, AnomalyLabel.ANOMALOUS))
        # EMA(0.5) should be close to 0.8 after 20 readings
        assert window.ema_score > 0.75

    def test_mean_score_calculation(self):
        """mean_score should average all scores in the current window."""
        window = MachineAnomalyWindow(machine_id="M-001", window_size=4)
        for score in [0.2, 0.4, 0.6, 0.8]:
            window.add(make_result("M-001", score))
        assert window.mean_score == pytest.approx(0.5)

    def test_get_window_summary_structure(self):
        """Window summary should contain all expected keys."""
        window = MachineAnomalyWindow(machine_id="X-001")
        window.add(make_result("X-001", 0.5, AnomalyLabel.ANOMALOUS))
        summary = window.get_window_summary()
        for key in ["machine_id", "reading_count", "window_size", "anomaly_ratio",
                    "mean_score", "ema_score", "is_sustained_anomaly", "alert_ratio_threshold"]:
            assert key in summary, f"Missing key: {key}"


# ---------------------------------------------------------------------------
# WindowedAnomalyAggregator tests
# ---------------------------------------------------------------------------

class TestWindowedAnomalyAggregator:

    def test_should_alert_false_before_warmup(self):
        """Aggregator must return False for unknown or cold machines."""
        agg = WindowedAnomalyAggregator(window_size=30, min_readings_before_alert=10)
        assert not agg.should_alert("UNKNOWN-001")
        # Record 5 anomalous readings — still below warmup
        for _ in range(5):
            agg.record(make_result("AGV-001", 0.9, AnomalyLabel.ANOMALOUS))
        assert not agg.should_alert("AGV-001")

    def test_should_alert_true_after_sustained_anomaly(self):
        """Aggregator should confirm alert when ratio threshold is met after warmup."""
        agg = WindowedAnomalyAggregator(
            window_size=20,
            min_readings_before_alert=10,
            alert_ratio_threshold=0.50,
        )
        # 12 anomalous out of 20 → 60% > 50% threshold
        for _ in range(12):
            agg.record(make_result("PMP-001", 0.85, AnomalyLabel.ANOMALOUS))
        for _ in range(8):
            agg.record(make_result("PMP-001", 0.1, AnomalyLabel.NORMAL))
        assert agg.should_alert("PMP-001")

    def test_should_alert_false_transient_spike(self):
        """Single-reading spikes should not trigger alert (key fix from audit)."""
        agg = WindowedAnomalyAggregator(
            window_size=30,
            min_readings_before_alert=10,
            alert_ratio_threshold=0.40,
        )
        # 1 anomalous + 9 normal — well below threshold
        agg.record(make_result("CNC-001", 0.95, AnomalyLabel.ANOMALOUS))
        for _ in range(9):
            agg.record(make_result("CNC-001", 0.1, AnomalyLabel.NORMAL))
        assert not agg.should_alert("CNC-001"), "Transient spike must NOT trigger alert"

    def test_fleet_isolation(self):
        """Different machines have independent windows."""
        agg = WindowedAnomalyAggregator(
            window_size=20, min_readings_before_alert=10, alert_ratio_threshold=0.40
        )
        # Pump: fill with sustained anomaly
        for _ in range(15):
            agg.record(make_result("PMP-001", 0.9, AnomalyLabel.ANOMALOUS))
        # CNC: all normal
        for _ in range(15):
            agg.record(make_result("CNC-001", 0.1, AnomalyLabel.NORMAL))

        assert agg.should_alert("PMP-001")
        assert not agg.should_alert("CNC-001")

    def test_reset_machine_clears_window(self):
        """reset_machine should clear state so a machine stops alerting."""
        agg = WindowedAnomalyAggregator(
            window_size=10, min_readings_before_alert=5, alert_ratio_threshold=0.40
        )
        for _ in range(8):
            agg.record(make_result("ROB-001", 0.9, AnomalyLabel.ANOMALOUS))
        assert agg.should_alert("ROB-001")

        agg.reset_machine("ROB-001")
        assert not agg.should_alert("ROB-001")
        assert "ROB-001" not in agg.tracked_machines

    def test_reset_all_clears_fleet(self):
        """reset_all should remove all machine windows."""
        agg = WindowedAnomalyAggregator(window_size=10, min_readings_before_alert=5)
        for mid in ["A-001", "B-001", "C-001"]:
            for _ in range(5):
                agg.record(make_result(mid, 0.9, AnomalyLabel.ANOMALOUS))
        assert len(agg.tracked_machines) == 3
        agg.reset_all()
        assert len(agg.tracked_machines) == 0

    def test_get_window_summary_returns_none_for_unknown(self):
        agg = WindowedAnomalyAggregator()
        assert agg.get_window_summary("UNKNOWN") is None

    def test_get_all_summaries(self):
        """get_all_summaries should return one entry per tracked machine."""
        agg = WindowedAnomalyAggregator()
        for mid in ["M1", "M2", "M3"]:
            agg.record(make_result(mid, 0.5))
        summaries = agg.get_all_summaries()
        assert len(summaries) == 3
        machine_ids = {s["machine_id"] for s in summaries}
        assert machine_ids == {"M1", "M2", "M3"}
