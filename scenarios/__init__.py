"""
Fault scenarios package for systematic failure simulation.
"""

from scenarios.fault_scenarios import (
    FaultScenario,
    FaultType,
    FaultSeverity,
    FaultLifecycleState,
)
from scenarios.manager import FaultScenarioManager, create_standard_scenarios
from scenarios.models import ScenarioStateRecord
from scenarios.repository import ScenarioStateRepository

__all__ = [
    "FaultScenario",
    "FaultType",
    "FaultSeverity",
    "FaultLifecycleState",
    "FaultScenarioManager",
    "create_standard_scenarios",
    "ScenarioStateRecord",
    "ScenarioStateRepository",
]
