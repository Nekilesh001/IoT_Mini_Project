"""
Core machine representation composing machine profile, state machine, physics engine, and fault hooks.
"""

from datetime import datetime, timezone
import random
from typing import Any, Dict, Optional
import uuid

from simulator.core.domain import (
    MachineProfile, MachineType, OperatingState, HealthState, ProtocolMetadata,
    SimulationGroundTruth, TelemetrySnapshot
)
from simulator.states.state_machine import MachineStateMachine
from simulator.degradation.degradation_model import DegradationModel
from simulator.process_models.base import MachineBehaviorStrategy
from simulator.process_models.strategies import STRATEGY_REGISTRY


class BaseMachine:
    """
    Simulated industrial machine unit.
    Integrates machine definition, state machine, continuous degradation, and strategy execution.
    """

    def __init__(
        self,
        profile: MachineProfile,
        strategy: Optional[MachineBehaviorStrategy] = None,
        seed: Optional[int] = None
    ):
        self._profile: MachineProfile = profile
        self._strategy: MachineBehaviorStrategy = strategy or STRATEGY_REGISTRY[profile.machine_type.value]
        self._state_machine: MachineStateMachine = MachineStateMachine(OperatingState.OFF)
        self._degradation: DegradationModel = DegradationModel()
        self._operating_load: float = profile.nominal_load
        self._sequence_counter: int = 0
        self._time_elapsed_seconds: float = 0.0
        self._seed: Optional[int] = seed
        self._rng: random.Random = random.Random(seed)
        self._scenario_id: str = "NORMAL_OPERATION"
        self._fault_label: Optional[str] = None

    @property
    def machine_id(self) -> str:
        return self._profile.machine_id

    @property
    def machine_type(self) -> MachineType:
        return self._profile.machine_type

    @property
    def protocol_metadata(self) -> ProtocolMetadata:
        return self._profile.protocol_metadata

    @property
    def profile(self) -> MachineProfile:
        return self._profile

    @property
    def operating_state(self) -> OperatingState:
        return self._state_machine.current_state

    @property
    def health_state(self) -> HealthState:
        return MachineStateMachine.derive_health_state(
            self._degradation.degradation_level,
            self._degradation.active_conditions
        )

    @property
    def operating_load(self) -> float:
        return self._operating_load

    @operating_load.setter
    def operating_load(self, load_pct: float) -> None:
        self._operating_load = max(0.0, min(150.0, float(load_pct)))

    @property
    def sequence_counter(self) -> int:
        return self._sequence_counter

    def set_sequence_counter(self, count: int) -> None:
        """Set the sequence counter for this machine."""
        self._sequence_counter = max(0, int(count))

    def set_seed(self, seed: Optional[int]) -> None:
        self._seed = seed
        self._rng = random.Random(seed)

    def set_operating_state(self, target_state: OperatingState) -> None:
        """Set machine operating state using state transition rules."""
        self._state_machine.transition_to(target_state)

    def force_operating_state(self, target_state: OperatingState) -> None:
        """Administrative force state override."""
        self._state_machine.force_state(target_state)

    def set_operating_load(self, load_pct: float) -> None:
        self.operating_load = load_pct

    def set_degradation(self, level: float) -> None:
        self._degradation.set_degradation(level)

    def apply_condition(self, condition_name: str, severity: float = 50.0) -> None:
        """Fault hook: Inject or update an internal simulation fault condition."""
        self._degradation.apply_condition(condition_name, severity)
        self._fault_label = condition_name

    def remove_condition(self, condition_name: str) -> None:
        self._degradation.remove_condition(condition_name)

    def inject_internal_condition(self, condition_name: str, parameters: Optional[Dict[str, Any]] = None) -> None:
        """Extensible internal fault hook interface."""
        severity = float((parameters or {}).get("severity", 50.0))
        self.apply_condition(condition_name, severity)

    def set_scenario_id(self, scenario_id: str) -> None:
        self._scenario_id = scenario_id

    def get_ground_truth(self) -> SimulationGroundTruth:
        return SimulationGroundTruth(
            degradation_level=self._degradation.degradation_level,
            scenario_id=self._scenario_id,
            fault_label=self._fault_label,
            active_conditions=self._degradation.active_conditions,
            hidden_wear_counter=self._degradation.hidden_wear_counter
        )

    def step(self, time_delta_seconds: float = 1.0) -> None:
        """
        Advance simulation clock by time_delta_seconds.
        Updates physics state, wear dynamics, and increments event sequence.
        """
        self._time_elapsed_seconds += time_delta_seconds
        self._sequence_counter += 1
        self._degradation.step(self.operating_state, self.operating_load, time_delta_seconds)

    def generate_snapshot(self, event_id: Optional[str] = None, timestamp: Optional[str] = None) -> TelemetrySnapshot:
        """
        Generate a telemetry snapshot containing public measurements and isolated ground-truth.
        """
        measurements = self._strategy.calculate_telemetry(
            profile=self._profile,
            operating_state=self.operating_state,
            load_pct=self._operating_load,
            degradation=self._degradation,
            time_elapsed_seconds=self._time_elapsed_seconds,
            rng=self._rng
        )

        evt_id = event_id or f"evt_{uuid.UUID(int=self._rng.getrandbits(128))}"
        ts = timestamp or datetime.now(timezone.utc).isoformat()

        return TelemetrySnapshot(
            schema_version="1.0.0",
            event_id=evt_id,
            machine_id=self.machine_id,
            machine_type=self.machine_type.value,
            protocol_metadata=self.protocol_metadata.value,
            timestamp=ts,
            sequence=self._sequence_counter,
            operating_state=self.operating_state.value,
            health_state=self.health_state.value,
            public_measurements=measurements,
            ground_truth=self.get_ground_truth()
        )
