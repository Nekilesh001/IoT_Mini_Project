"""
Unit tests for telemetry snapshot generation, sequence tracking, and value bounding.
"""

from simulator.runtime.factory_runtime import FactorySimulator
from simulator.core.domain import OperatingState


def test_telemetry_snapshot_generation_and_sequence():
    factory = FactorySimulator(seed=42)
    factory.start()

    m = factory.get_machine("CNC-001")
    initial_seq = m.sequence_counter

    m.step(1.0)
    snap1 = m.generate_snapshot()
    assert snap1.sequence == initial_seq + 1
    assert snap1.machine_id == "CNC-001"
    assert snap1.operating_state == OperatingState.RUNNING.value
    assert isinstance(snap1.public_measurements, dict)
    assert len(snap1.public_measurements) > 0

    m.step(1.0)
    snap2 = m.generate_snapshot()
    assert snap2.sequence == snap1.sequence + 1


def test_measurement_physical_bounds_under_normal_operation():
    factory = FactorySimulator(seed=42)
    factory.start()
    factory.step(1.0)

    snapshots = factory.collect_telemetry()
    for snap in snapshots:
        m = factory.get_machine(snap.machine_id)
        for sig_def in m.profile.signals:
            if sig_def.name in snap.public_measurements:
                val = snap.public_measurements[sig_def.name]
                if isinstance(val, (int, float)) and sig_def.min_value is not None and sig_def.max_value is not None:
                    # Allow minor stochastic margin
                    margin = (sig_def.max_value - sig_def.min_value) * 0.1
                    assert sig_def.min_value - margin <= val <= sig_def.max_value + margin, (
                        f"Signal '{sig_def.name}' value {val} out of expected bounds "
                        f"[{sig_def.min_value}, {sig_def.max_value}] for {snap.machine_id}."
                    )
