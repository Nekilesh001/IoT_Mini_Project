"""
Unit tests for FaultScenario and FaultScenarioManager.
Tests scenario registration, lifecycle, state advance, and simulator condition hook integration.
"""

import pytest
from simulator.runtime.factory_runtime import FactorySimulator
from scenarios.fault_scenarios import FaultScenario, FaultType, FaultSeverity, FaultLifecycleState
from scenarios.manager import FaultScenarioManager, create_standard_scenarios


def test_standard_scenarios_catalog():
    scenarios = create_standard_scenarios()
    assert len(scenarios) >= 10
    scenario_ids = list(scenarios.keys())
    assert "PUMP_BEARING_WEAR" in scenario_ids
    assert "CONVEYOR_BELT_JAM" in scenario_ids
    assert "CNC_SPINDLE_OVERHEAT" in scenario_ids
    assert "CHILLER_LOW_FLOW" in scenario_ids
    assert "AGV_LOW_BATTERY" in scenario_ids


def test_fault_scenario_manager_lifecycle():
    factory = FactorySimulator()
    factory.start()
    manager = FaultScenarioManager(factory)
    scenarios = create_standard_scenarios()
    manager.register_scenarios(scenarios)

    # 1. Start scenario
    active_scenario = manager.start_scenario("CONVEYOR_BELT_JAM")
    assert active_scenario.state == FaultLifecycleState.ACTIVE
    assert active_scenario.scenario_id == "CONVEYOR_BELT_JAM"
    assert "CONVEYOR_BELT_JAM" in manager.get_active_scenarios()

    # Verify machine received condition
    conv = factory.get_machine("CON-001")
    assert conv is not None
    assert "jammed" in conv._degradation.active_conditions

    # 2. Advance ticks
    manager.advance_scenarios(dt_seconds=1.0)
    assert active_scenario.elapsed_seconds == 1.0

    # 3. Stop scenario
    stopped = manager.stop_scenario("CONVEYOR_BELT_JAM")
    assert stopped.state == FaultLifecycleState.RESOLVED
    assert len(manager.get_active_scenarios()) == 0
    assert "jammed" not in conv._degradation.active_conditions


def test_unknown_scenario_handling():
    factory = FactorySimulator()
    manager = FaultScenarioManager(factory)

    with pytest.raises(KeyError, match="not found"):
        manager.start_scenario("NON_EXISTENT_FAULT")

    with pytest.raises(KeyError):
        manager.stop_scenario("NON_EXISTENT_FAULT")
