"""
Fault taxonomy and scenario models for systematic simulation fault injection.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import uuid

from simulator.runtime.factory_runtime import FactorySimulator


class FaultType(str, Enum):
    MACHINE_FAULT = "MACHINE_FAULT"
    SENSOR_FAULT = "SENSOR_FAULT"
    PROTOCOL_FAULT = "PROTOCOL_FAULT"
    NETWORK_FAULT = "NETWORK_FAULT"
    EDGE_FAULT = "EDGE_FAULT"
    CLOUD_FAULT = "CLOUD_FAULT"


class FaultSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class FaultLifecycleState(str, Enum):
    IDLE = "IDLE"
    ACTIVE = "ACTIVE"
    RECOVERING = "RECOVERING"
    RESOLVED = "RESOLVED"


@dataclass
class FaultScenario:
    """
    Represents a systematic fault scenario injected into a simulated machine.
    Controls machine degradation and physical condition hooks without directly crafting raw telemetry.
    """
    scenario_id: str
    machine_id: str
    machine_type: str
    fault_type: FaultType
    fault_code: str
    title: str
    description: str
    severity: FaultSeverity
    is_progressive: bool = False
    duration_ticks: Optional[int] = None
    target_condition: str = "general_fault"
    max_severity_pct: float = 100.0

    # Runtime state
    state: FaultLifecycleState = FaultLifecycleState.IDLE
    current_tick: int = 0
    start_time: Optional[str] = None
    end_time: Optional[str] = None

    def start(self, factory: FactorySimulator) -> None:
        """Activates the fault condition on the target machine."""
        self.state = FaultLifecycleState.ACTIVE
        self.current_tick = 0
        self.start_time = datetime.now(timezone.utc).isoformat()
        self.end_time = None

        machine = factory.get_machine(self.machine_id)
        if machine:
            machine.set_scenario_id(self.scenario_id)
            initial_sev = 10.0 if self.is_progressive else self.max_severity_pct
            machine.apply_condition(self.target_condition, severity=initial_sev)
            if self.is_progressive:
                machine.set_degradation(initial_sev)

    def advance(self, factory: FactorySimulator, dt_seconds: float = 1.0, **kwargs) -> None:
        """Advances the scenario tick for progressive wear or duration tracking."""
        if self.state != FaultLifecycleState.ACTIVE:
            return

        self.current_tick += 1
        if not hasattr(self, "elapsed_seconds"):
            self.elapsed_seconds = 0.0
        self.elapsed_seconds += dt_seconds

        machine = factory.get_machine(self.machine_id)
        if not machine:
            return

        if self.is_progressive:
            # Gradually increase condition severity
            step_inc = max(5.0, (self.max_severity_pct - 10.0) / 10.0)
            current_sev = min(self.max_severity_pct, 10.0 + (self.current_tick * step_inc))
            machine.apply_condition(self.target_condition, severity=current_sev)
            machine.set_degradation(current_sev)

        if self.duration_ticks and self.current_tick >= self.duration_ticks:
            self.stop(factory)

    def stop(self, factory: FactorySimulator) -> None:
        """Resolves the fault condition and restores normal machine behavior."""
        self.state = FaultLifecycleState.RESOLVED
        self.end_time = datetime.now(timezone.utc).isoformat()

        machine = factory.get_machine(self.machine_id)
        if machine:
            machine.remove_condition(self.target_condition)
            machine.set_degradation(0.0)
            machine.set_scenario_id("NORMAL")


    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "machine_id": self.machine_id,
            "machine_type": self.machine_type,
            "fault_type": self.fault_type.value,
            "fault_code": self.fault_code,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "is_progressive": self.is_progressive,
            "duration_ticks": self.duration_ticks,
            "state": self.state.value,
            "current_tick": self.current_tick,
            "start_time": self.start_time,
            "end_time": self.end_time,
        }
