"""
Tests for simulator/degradation/degradation_model.py
Covers: C5 (recovery lowers degradation), wear physics, condition injection.
"""

import pytest
from simulator.core.domain import OperatingState
from simulator.degradation.degradation_model import DegradationModel


class TestDegradationModel:

    def test_running_state_increases_degradation(self):
        model = DegradationModel(initial_level=0.0, wear_rate_per_hour=1.0)
        model.step(OperatingState.RUNNING, operating_load=100.0, time_delta_seconds=3600.0)
        assert model.degradation_level > 0.0

    def test_warning_state_increases_faster_than_running(self):
        """WARNING state should accelerate wear faster than RUNNING at same load."""
        m_run = DegradationModel(initial_level=0.0, wear_rate_per_hour=1.0)
        m_warn = DegradationModel(initial_level=0.0, wear_rate_per_hour=1.0)
        m_run.step(OperatingState.RUNNING, 100.0, 3600.0)
        m_warn.step(OperatingState.WARNING, 100.0, 3600.0)
        assert m_warn.degradation_level > m_run.degradation_level

    def test_maintenance_reduces_degradation(self):
        """C5: MAINTENANCE state must reduce degradation level (not leave it unchanged)."""
        model = DegradationModel(initial_level=50.0)
        initial = model.degradation_level
        model.step(OperatingState.MAINTENANCE, operating_load=0.0, time_delta_seconds=3600.0)
        assert model.degradation_level < initial, (
            "Maintenance must reduce degradation (was pass before fix)"
        )

    def test_recovery_reduces_degradation(self):
        """C5: RECOVERY state must also reduce degradation."""
        model = DegradationModel(initial_level=30.0)
        initial = model.degradation_level
        model.step(OperatingState.RECOVERY, operating_load=0.0, time_delta_seconds=3600.0)
        assert model.degradation_level < initial

    def test_maintenance_does_not_go_below_zero(self):
        """Degradation must never go negative during maintenance."""
        model = DegradationModel(initial_level=0.01)
        for _ in range(1000):
            model.step(OperatingState.MAINTENANCE, 0.0, 3600.0)
        assert model.degradation_level >= 0.0

    def test_degradation_capped_at_100(self):
        """Degradation must never exceed 100%."""
        model = DegradationModel(initial_level=99.0, wear_rate_per_hour=100.0)
        model.step(OperatingState.RUNNING, 100.0, 3600.0)
        assert model.degradation_level <= 100.0

    def test_off_state_does_not_change_degradation(self):
        """OFF state: no wear and no repair."""
        model = DegradationModel(initial_level=50.0)
        initial = model.degradation_level
        model.step(OperatingState.OFF, operating_load=0.0, time_delta_seconds=3600.0)
        assert model.degradation_level == initial

    def test_apply_and_remove_condition(self):
        model = DegradationModel()
        model.apply_condition("bearing_wear", severity=80.0)
        assert model.get_condition_severity("bearing_wear") == pytest.approx(80.0)
        model.remove_condition("bearing_wear")
        assert model.get_condition_severity("bearing_wear") == pytest.approx(0.0)

    def test_hidden_wear_counter_monotonically_increases_during_running(self):
        model = DegradationModel()
        prev = model.hidden_wear_counter
        for _ in range(5):
            model.step(OperatingState.RUNNING, 100.0, 60.0)
            assert model.hidden_wear_counter > prev
            prev = model.hidden_wear_counter

    def test_full_maintenance_cycle_lowers_degradation_significantly(self):
        """After 10 hours of maintenance on a 50% degraded machine, it should drop noticeably."""
        model = DegradationModel(initial_level=50.0)
        # 10 hours of maintenance = 36000 seconds
        model.step(OperatingState.MAINTENANCE, 0.0, 36000.0)
        # Expect at least 15% reduction (2%/hour * 10 hours = 20%)
        assert model.degradation_level <= 35.0
