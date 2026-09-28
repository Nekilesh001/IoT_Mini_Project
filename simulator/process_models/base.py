"""
Base interface for machine telemetry behavior strategies.
"""

from abc import ABC, abstractmethod
import random
from typing import Any, Dict
from simulator.core.domain import MachineProfile, OperatingState
from simulator.degradation.degradation_model import DegradationModel


class MachineBehaviorStrategy(ABC):
    """
    Abstract base class for machine-specific telemetry calculation strategies.
    Derives dynamic measurements strictly from physical state, load, state, and degradation.
    """

    @abstractmethod
    def calculate_telemetry(
        self,
        profile: MachineProfile,
        operating_state: OperatingState,
        load_pct: float,
        degradation: DegradationModel,
        time_elapsed_seconds: float,
        rng: random.Random
    ) -> Dict[str, Any]:
        """
        Calculate dictionary of public signal measurements for a simulation tick.
        """
        pass
