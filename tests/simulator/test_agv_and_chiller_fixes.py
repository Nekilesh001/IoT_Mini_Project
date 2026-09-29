"""
Tests for AGV battery charge/discharge cycle (Fix C4) and
chiller signal name fix (Fix C3).
"""

import pytest
from simulator.core.domain import OperatingState, MachineProfile, MachineType, ProtocolMetadata
from simulator.degradation.degradation_model import DegradationModel
from simulator.process_models.strategies import AGVBehavior, ChillerBehavior
import random


def make_profile(machine_id: str, mtype: MachineType) -> MachineProfile:
    return MachineProfile(
        machine_id=machine_id,
        machine_type=mtype,
        plant_id="PLANT_01",
        line_id="LINE_A",
        protocol_metadata=ProtocolMetadata.MQTT,
        nominal_load=50.0,
    )


def make_deg() -> DegradationModel:
    return DegradationModel()


class TestAGVBatteryRecharge:
    """Fix C4: AGV SOC must not drain to zero permanently."""

    def test_soc_starts_at_85(self):
        strategy = AGVBehavior()
        profile = make_profile("AGV-001", MachineType.AUTONOMOUS_MOBILE_ROBOT)
        # Clear class-level state for this test
        AGVBehavior._soc_state.clear()
        AGVBehavior._charging.clear()
        rng = random.Random(42)
        result = strategy.calculate_telemetry(
            profile, OperatingState.RUNNING, 50.0, make_deg(), 0.0, rng
        )
        assert result["battery_soc_pct"] == pytest.approx(85.0, abs=0.5)

    def test_soc_does_not_fall_below_zero(self):
        """SOC must never go below 0%."""
        strategy = AGVBehavior()
        profile = make_profile("AGV-DRAIN", MachineType.AUTONOMOUS_MOBILE_ROBOT)
        AGVBehavior._soc_state.clear()
        AGVBehavior._charging.clear()
        rng = random.Random(1)
        result = None
        for t in range(10000):
            result = strategy.calculate_telemetry(
                profile, OperatingState.RUNNING, 50.0, make_deg(), float(t), rng
            )
        assert result["battery_soc_pct"] >= 0.0

    def test_soc_recharges_when_docked(self):
        """After draining to low threshold, AGV should start charging."""
        strategy = AGVBehavior()
        profile = make_profile("AGV-CHARGE", MachineType.AUTONOMOUS_MOBILE_ROBOT)
        AGVBehavior._soc_state.clear()
        AGVBehavior._charging.clear()
        rng = random.Random(99)

        # Force a low SOC state
        key = id(profile)
        AGVBehavior._soc_state[key] = 15.0  # below LOW_BATTERY_SOC=20
        AGVBehavior._charging[key] = False

        result = strategy.calculate_telemetry(
            profile, OperatingState.RUNNING, 50.0, make_deg(), 1.0, rng
        )
        # Should now be charging
        assert result["docking_state"] == "CHARGING"
        assert AGVBehavior._charging[key] is True

    def test_soc_rises_when_charging(self):
        """SOC should increase step by step while charging."""
        strategy = AGVBehavior()
        profile = make_profile("AGV-SOC-RISE", MachineType.AUTONOMOUS_MOBILE_ROBOT)
        AGVBehavior._soc_state.clear()
        AGVBehavior._charging.clear()
        rng = random.Random(7)

        key = id(profile)
        AGVBehavior._soc_state[key] = 15.0
        AGVBehavior._charging[key] = True  # Already charging

        soc_readings = []
        for t in range(20):
            result = strategy.calculate_telemetry(
                profile, OperatingState.RUNNING, 50.0, make_deg(), float(t), rng
            )
            soc_readings.append(result["battery_soc_pct"])

        # SOC should be strictly increasing while charging
        assert soc_readings[-1] > soc_readings[0], "SOC must rise during charging"

    def test_soc_stops_charging_at_target(self):
        """AGV should stop charging once SOC reaches CHARGE_TARGET_SOC (90%)."""
        strategy = AGVBehavior()
        profile = make_profile("AGV-FULL", MachineType.AUTONOMOUS_MOBILE_ROBOT)
        AGVBehavior._soc_state.clear()
        AGVBehavior._charging.clear()
        rng = random.Random(5)

        key = id(profile)
        AGVBehavior._soc_state[key] = 89.5
        AGVBehavior._charging[key] = True

        # Multiple steps to cross the threshold
        result = None
        for t in range(5):
            result = strategy.calculate_telemetry(
                profile, OperatingState.RUNNING, 50.0, make_deg(), float(t), rng
            )

        # Should no longer be charging once SOC >= 90
        if AGVBehavior._soc_state[key] >= AGVBehavior._CHARGE_TARGET_SOC:
            assert AGVBehavior._charging[key] is False


class TestChillerSignalName:
    """Fix C3: Chiller must output 'coolant_flow_rate_l_min' not 'flow_rate_l_min'."""

    def test_chiller_outputs_correct_flow_field_name(self):
        strategy = ChillerBehavior()
        profile = make_profile("CHL-001", MachineType.INDUSTRIAL_CHILLER)
        rng = random.Random(0)
        result = strategy.calculate_telemetry(
            profile, OperatingState.RUNNING, 75.0, make_deg(), 100.0, rng
        )
        assert "coolant_flow_rate_l_min" in result, (
            "Chiller must use 'coolant_flow_rate_l_min' to match alert rule signal name"
        )
        assert "flow_rate_l_min" not in result, (
            "Old incorrect key 'flow_rate_l_min' must NOT be present"
        )

    def test_chiller_flow_is_positive_when_running(self):
        strategy = ChillerBehavior()
        profile = make_profile("CHL-001", MachineType.INDUSTRIAL_CHILLER)
        rng = random.Random(0)
        result = strategy.calculate_telemetry(
            profile, OperatingState.RUNNING, 75.0, make_deg(), 100.0, rng
        )
        assert result["coolant_flow_rate_l_min"] > 0.0

    def test_chiller_flow_is_zero_when_off(self):
        strategy = ChillerBehavior()
        profile = make_profile("CHL-001", MachineType.INDUSTRIAL_CHILLER)
        rng = random.Random(0)
        result = strategy.calculate_telemetry(
            profile, OperatingState.OFF, 0.0, make_deg(), 0.0, rng
        )
        assert result["coolant_flow_rate_l_min"] == pytest.approx(0.0)
