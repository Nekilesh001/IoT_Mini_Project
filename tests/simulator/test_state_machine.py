"""
Unit tests for operating state machine transitions and health state derivation.
"""

import pytest
from simulator.core.domain import OperatingState, HealthState, InvalidStateTransitionError
from simulator.states.state_machine import MachineStateMachine


def test_valid_state_transitions():
    sm = MachineStateMachine(OperatingState.OFF)
    assert sm.current_state == OperatingState.OFF

    sm.transition_to(OperatingState.STARTING)
    assert sm.current_state == OperatingState.STARTING

    sm.transition_to(OperatingState.IDLE)
    assert sm.current_state == OperatingState.IDLE

    sm.transition_to(OperatingState.RUNNING)
    assert sm.current_state == OperatingState.RUNNING

    sm.transition_to(OperatingState.WARNING)
    assert sm.current_state == OperatingState.WARNING

    sm.transition_to(OperatingState.FAULT)
    assert sm.current_state == OperatingState.FAULT

    sm.transition_to(OperatingState.MAINTENANCE)
    assert sm.current_state == OperatingState.MAINTENANCE

    sm.transition_to(OperatingState.RECOVERY)
    assert sm.current_state == OperatingState.RECOVERY


def test_invalid_state_transitions():
    sm = MachineStateMachine(OperatingState.OFF)
    with pytest.raises(InvalidStateTransitionError):
        sm.transition_to(OperatingState.RUNNING)

    with pytest.raises(InvalidStateTransitionError):
        sm.transition_to(OperatingState.MAINTENANCE)


def test_health_state_derivation():
    assert MachineStateMachine.derive_health_state(0.0, {}) == HealthState.HEALTHY
    assert MachineStateMachine.derive_health_state(40.0, {}) == HealthState.WARNING
    assert MachineStateMachine.derive_health_state(80.0, {}) == HealthState.FAULT
    assert MachineStateMachine.derive_health_state(10.0, {"bearing_wear": 85.0}) == HealthState.FAULT
