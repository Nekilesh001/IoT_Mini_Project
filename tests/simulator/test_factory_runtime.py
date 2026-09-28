"""
Unit tests for FactorySimulator runtime operations.
"""

from simulator.runtime.factory_runtime import FactorySimulator
from simulator.core.domain import OperatingState


def test_factory_start_stop_step():
    factory = FactorySimulator(seed=42)
    assert not factory.is_running
    assert factory.total_ticks == 0

    factory.start()
    assert factory.is_running
    for m in factory.get_all_machines():
        assert m.operating_state == OperatingState.RUNNING

    factory.step(1.0)
    assert factory.total_ticks == 1

    snapshots = factory.collect_telemetry()
    assert len(snapshots) == 12

    factory.stop()
    assert not factory.is_running
    for m in factory.get_all_machines():
        assert m.operating_state == OperatingState.OFF
