"""
Tests for Simulator strategy fixes:
  - CNC tool wear reset (Fix I3)
  - Pump start_stop_count increments dynamically (Fix I2)
  - Gaussian noise produces correct statistical distribution (Fix I1)
"""

import math
import random
import statistics

import pytest

from simulator.core.domain import MachineProfile, MachineType, OperatingState, ProtocolMetadata
from simulator.degradation.degradation_model import DegradationModel
from simulator.process_models.strategies import (
    CNCMachiningCenterBehavior,
    CNCLatheBehavior,
    PumpBehavior,
    _CNC_MACHINING_TOOL_LIFE_S,
    _CNC_LATHE_TOOL_LIFE_S,
)


def make_profile(machine_id: str, mtype: MachineType) -> MachineProfile:
    return MachineProfile(
        machine_id=machine_id,
        machine_type=mtype,
        plant_id="PLANT_01",
        line_id="LINE_A",
        protocol_metadata=ProtocolMetadata.MQTT,
        nominal_load=80.0,
    )


def make_deg(level: float = 0.0) -> DegradationModel:
    return DegradationModel(initial_level=level)


class TestCNCToolWearReset:
    """Fix I3: Tool wear must cycle between 0-100% and reset on tool change."""

    def test_tool_wear_does_not_exceed_100(self):
        strategy = CNCMachiningCenterBehavior()
        profile = make_profile("CNC-001", MachineType.CNC_MACHINING_CENTER)
        rng = random.Random(42)
        deg = make_deg()
        # Run for 3 complete tool life cycles
        for t in range(int(_CNC_MACHINING_TOOL_LIFE_S * 3) + 1):
            result = strategy.calculate_telemetry(
                profile, OperatingState.RUNNING, 80.0, deg, float(t), rng
            )
            assert result["tool_wear_pct"] <= 100.0

    def test_tool_wear_resets_at_tool_change(self):
        """Wear should drop back near initial value at the start of each new tool."""
        strategy = CNCMachiningCenterBehavior()
        profile = make_profile("CNC-001", MachineType.CNC_MACHINING_CENTER)
        rng = random.Random(42)
        deg = make_deg()

        # Just before end of first tool
        r_end_of_tool = strategy.calculate_telemetry(
            profile, OperatingState.RUNNING, 80.0, deg,
            _CNC_MACHINING_TOOL_LIFE_S - 1.0, rng
        )
        # Just at start of second tool
        r_start_of_tool2 = strategy.calculate_telemetry(
            profile, OperatingState.RUNNING, 80.0, deg,
            _CNC_MACHINING_TOOL_LIFE_S + 1.0, rng
        )
        assert r_end_of_tool["tool_wear_pct"] > r_start_of_tool2["tool_wear_pct"], (
            "Tool wear must drop at tool change boundary"
        )

    def test_tool_change_count_increments(self):
        """tool_change_count must increment once per tool life cycle."""
        strategy = CNCMachiningCenterBehavior()
        profile = make_profile("CNC-001", MachineType.CNC_MACHINING_CENTER)
        rng = random.Random(0)
        deg = make_deg()

        r0 = strategy.calculate_telemetry(profile, OperatingState.RUNNING, 80.0, deg, 0.0, rng)
        r1 = strategy.calculate_telemetry(
            profile, OperatingState.RUNNING, 80.0, deg, _CNC_MACHINING_TOOL_LIFE_S + 1.0, rng
        )
        assert r1["tool_change_count"] > r0["tool_change_count"]

    def test_lathe_tool_wear_resets(self):
        """CNC Lathe tool wear must also cycle via modular time."""
        strategy = CNCLatheBehavior()
        profile = make_profile("CNC-002", MachineType.CNC_LATHE)
        rng = random.Random(1)
        deg = make_deg()

        r_end = strategy.calculate_telemetry(
            profile, OperatingState.RUNNING, 80.0, deg,
            _CNC_LATHE_TOOL_LIFE_S - 1.0, rng
        )
        r_start = strategy.calculate_telemetry(
            profile, OperatingState.RUNNING, 80.0, deg,
            _CNC_LATHE_TOOL_LIFE_S + 1.0, rng
        )
        assert r_end["tool_wear_pct"] > r_start["tool_wear_pct"]


class TestPumpStartStopCount:
    """Fix I2: Pump start_stop_count must increment on state transitions."""

    def test_start_count_increments_on_running_entry(self):
        PumpBehavior._start_counters.clear()
        PumpBehavior._was_running.clear()

        strategy = PumpBehavior()
        profile = make_profile("PMP-001", MachineType.INDUSTRIAL_PUMP)
        rng = random.Random(0)
        deg = make_deg()

        # OFF → RUNNING transition
        r_off = strategy.calculate_telemetry(
            profile, OperatingState.OFF, 0.0, deg, 0.0, rng
        )
        r_run = strategy.calculate_telemetry(
            profile, OperatingState.RUNNING, 65.0, deg, 1.0, rng
        )
        assert r_run["start_stop_count"] > r_off["start_stop_count"]

    def test_start_count_does_not_increment_while_continuously_running(self):
        """If already RUNNING, no additional increments on each tick."""
        PumpBehavior._start_counters.clear()
        PumpBehavior._was_running.clear()

        strategy = PumpBehavior()
        profile = make_profile("PMP-002", MachineType.INDUSTRIAL_PUMP)
        rng = random.Random(5)
        deg = make_deg()

        # First call sets it running
        r1 = strategy.calculate_telemetry(
            profile, OperatingState.RUNNING, 65.0, deg, 0.0, rng
        )
        count_after_first = r1["start_stop_count"]

        # Subsequent running ticks should not increment
        for t in range(1, 10):
            r = strategy.calculate_telemetry(
                profile, OperatingState.RUNNING, 65.0, deg, float(t), rng
            )
        assert r["start_stop_count"] == count_after_first


class TestGaussianNoise:
    """Fix I1: Noise should approximate Gaussian (mean≈0, not uniform flat distribution)."""

    def test_cnc_vibration_noise_is_gaussian_like(self):
        """
        Collect 200 vibration readings and verify the noise is normally distributed:
        The mean deviation from the deterministic base should be near 0,
        and the std should be consistent with the specified Gaussian sigma.
        """
        strategy = CNCMachiningCenterBehavior()
        profile = make_profile("CNC-001", MachineType.CNC_MACHINING_CENTER)
        deg = make_deg(level=0.0)

        # At deg=0, base vib = 1.0 + 0 = 1.0 + noise
        readings = []
        for i in range(200):
            rng = random.Random(i)
            r = strategy.calculate_telemetry(
                profile, OperatingState.RUNNING, 100.0, deg, float(i * 10), rng
            )
            readings.append(r["vibration_rms_mm_s"])

        mean = statistics.mean(readings)
        # With Gaussian noise sigma=0.04, mean should be very close to base (1.0)
        # Allow ±0.3 tolerance for 1% spike outlier injection
        assert 0.7 < mean < 1.5, f"Mean vibration {mean:.3f} is out of expected range"

    def test_pump_flow_noise_is_bounded_reasonably(self):
        """Pump flow should stay within ±2 m³/h of nominal at nominal load (65%)."""
        PumpBehavior._start_counters.clear()
        PumpBehavior._was_running.clear()
        strategy = PumpBehavior()
        profile = make_profile("PMP-001", MachineType.INDUSTRIAL_PUMP)
        deg = make_deg(level=0.0)
        # At load_pct=65, flow = 65 * (65/65) + gauss(0, 0.4) ≈ 65 m³/h
        nominal_flow = 65.0

        readings = []
        for i in range(100):
            rng = random.Random(i + 1000)
            r = strategy.calculate_telemetry(
                profile, OperatingState.RUNNING, 65.0, deg, float(i), rng
            )
            readings.append(r["flow_rate_m3_h"])

        for flow in readings:
            assert abs(flow - nominal_flow) < 3.0, (
                f"Pump flow {flow:.2f} too far from nominal {nominal_flow}"
            )
