"""
Unit tests for causal physics, load dependency, and correlated degradation physics.
"""

from simulator.runtime.factory_runtime import FactorySimulator
from simulator.core.domain import OperatingState


def test_load_dependency_causality():
    factory = FactorySimulator(seed=42)
    factory.start()

    cnc = factory.get_machine("CNC-001")

    # Low load
    cnc.operating_load = 20.0
    cnc.step(1.0)
    snap_low = cnc.generate_snapshot()

    # High load
    cnc.operating_load = 90.0
    cnc.step(1.0)
    snap_high = cnc.generate_snapshot()

    # Spindle speed and spindle temperature must increase with load
    assert snap_high.public_measurements["spindle_speed_rpm"] > snap_low.public_measurements["spindle_speed_rpm"]
    assert snap_high.public_measurements["spindle_temperature_c"] > snap_low.public_measurements["spindle_temperature_c"]


def test_degradation_causal_correlation():
    factory = FactorySimulator(seed=42)
    factory.start()

    pump = factory.get_machine("PMP-001")

    # Baseline healthy step
    pump.set_degradation(0.0)
    pump.step(1.0)
    snap_healthy = pump.generate_snapshot()

    # Degraded step
    pump.set_degradation(75.0)
    pump.apply_condition("bearing_wear", severity=75.0)
    pump.step(1.0)
    snap_degraded = pump.generate_snapshot()

    # Bearing degradation must causally increase both bearing temperature and vibration RMS
    assert snap_degraded.public_measurements["bearing_temperature_c"] > snap_healthy.public_measurements["bearing_temperature_c"]
    assert snap_degraded.public_measurements["vibration_x_mm_s"] > snap_healthy.public_measurements["vibration_x_mm_s"]
