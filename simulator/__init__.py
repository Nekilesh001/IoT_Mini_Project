"""
Factory Simulation Core package.
"""

from simulator.core.domain import (
    OperatingState, HealthState, MachineType, ProtocolMetadata,
    SignalDefinition, MachineProfile, TelemetrySnapshot, SimulationGroundTruth
)
from simulator.core.machine import BaseMachine
from simulator.runtime.factory_runtime import FactorySimulator

__version__ = "1.0.0"
__all__ = [
    "OperatingState",
    "HealthState",
    "MachineType",
    "ProtocolMetadata",
    "SignalDefinition",
    "MachineProfile",
    "TelemetrySnapshot",
    "SimulationGroundTruth",
    "BaseMachine",
    "FactorySimulator",
]
