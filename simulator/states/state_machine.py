"""
Machine operating state machine and transition validation logic.
"""

from typing import Dict, Set
from simulator.core.domain import OperatingState, HealthState, InvalidStateTransitionError


class MachineStateMachine:
    """
    Manages operating state transitions and computes health state for simulated machines.
    """

    # Allowed state transition map
    VALID_TRANSITIONS: Dict[OperatingState, Set[OperatingState]] = {
        OperatingState.OFF: {OperatingState.STARTING},
        OperatingState.STARTING: {OperatingState.IDLE, OperatingState.RUNNING, OperatingState.FAULT},
        OperatingState.IDLE: {OperatingState.RUNNING, OperatingState.OFF, OperatingState.MAINTENANCE, OperatingState.FAULT},
        OperatingState.RUNNING: {OperatingState.IDLE, OperatingState.WARNING, OperatingState.FAULT, OperatingState.MAINTENANCE},
        OperatingState.WARNING: {OperatingState.RUNNING, OperatingState.FAULT, OperatingState.MAINTENANCE, OperatingState.IDLE},
        OperatingState.FAULT: {OperatingState.RECOVERY, OperatingState.MAINTENANCE},
        OperatingState.MAINTENANCE: {OperatingState.RECOVERY, OperatingState.OFF, OperatingState.IDLE},
        OperatingState.RECOVERY: {OperatingState.IDLE, OperatingState.RUNNING, OperatingState.OFF, OperatingState.FAULT},
    }

    def __init__(self, initial_state: OperatingState = OperatingState.OFF):
        self._current_operating_state: OperatingState = initial_state

    @property
    def current_state(self) -> OperatingState:
        return self._current_operating_state

    def can_transition_to(self, target_state: OperatingState) -> bool:
        if target_state == self._current_operating_state:
            return True
        allowed = self.VALID_TRANSITIONS.get(self._current_operating_state, set())
        return target_state in allowed

    def transition_to(self, target_state: OperatingState) -> None:
        """
        Transition machine to target operating state.
        Raises InvalidStateTransitionError if transition is not permitted.
        """
        if target_state == self._current_operating_state:
            return

        if not self.can_transition_to(target_state):
            raise InvalidStateTransitionError(
                f"Cannot transition machine from '{self._current_operating_state.value}' "
                f"to '{target_state.value}'."
            )

        self._current_operating_state = target_state

    def force_state(self, target_state: OperatingState) -> None:
        """Force state transition for initialization or administrative reset."""
        self._current_operating_state = target_state

    @staticmethod
    def derive_health_state(degradation_level: float, active_conditions: Dict[str, float]) -> HealthState:
        """
        Derive high-level health state from internal continuous degradation level (0-100)
        and active fault conditions.
        """
        has_critical_fault = any(v >= 80.0 for v in active_conditions.values())
        has_warning_condition = any(v >= 40.0 for v in active_conditions.values())

        if degradation_level >= 75.0 or has_critical_fault:
            return HealthState.FAULT
        elif degradation_level >= 35.0 or has_warning_condition:
            return HealthState.WARNING
        else:
            return HealthState.HEALTHY
