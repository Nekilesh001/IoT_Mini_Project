"""
Continuous degradation and internal fault condition model.
"""

from typing import Dict
from simulator.core.domain import OperatingState


class DegradationModel:
    """
    Simulates continuous internal degradation dynamics and manages fault hooks.
    This internal state is isolated from public telemetry.
    """

    def __init__(self, initial_level: float = 0.0, wear_rate_per_hour: float = 0.05):
        self._degradation_level: float = max(0.0, min(100.0, float(initial_level)))
        self._wear_rate_per_hour: float = wear_rate_per_hour
        self._hidden_wear_counter: float = 0.0
        self._active_conditions: Dict[str, float] = {}  # condition_name -> severity (0.0 to 100.0)

    @property
    def degradation_level(self) -> float:
        return self._degradation_level

    @degradation_level.setter
    def degradation_level(self, value: float) -> None:
        self._degradation_level = max(0.0, min(100.0, float(value)))

    @property
    def hidden_wear_counter(self) -> float:
        return self._hidden_wear_counter

    @property
    def active_conditions(self) -> Dict[str, float]:
        return dict(self._active_conditions)

    def set_degradation(self, level: float) -> None:
        self.degradation_level = level

    def apply_condition(self, condition_name: str, severity: float = 50.0) -> None:
        """Inject or update an internal fault condition with a given severity (0-100)."""
        self._active_conditions[condition_name] = max(0.0, min(100.0, float(severity)))

    def remove_condition(self, condition_name: str) -> None:
        """Clear an internal fault condition."""
        self._active_conditions.pop(condition_name, None)

    def clear_all_conditions(self) -> None:
        self._active_conditions.clear()

    def get_condition_severity(self, condition_name: str) -> float:
        return self._active_conditions.get(condition_name, 0.0)

    def step(self, operating_state: OperatingState, operating_load: float, time_delta_seconds: float) -> None:
        """
        Advance internal wear and degradation based on operating state and load.
        RUNNING/WARNING accumulate wear; MAINTENANCE/RECOVERY partially repair it.
        """
        if operating_state == OperatingState.RUNNING:
            load_factor = (operating_load / 100.0) ** 1.5
            wear = (self._wear_rate_per_hour / 3600.0) * time_delta_seconds * load_factor
            self._hidden_wear_counter += wear
            self._degradation_level = min(100.0, self._degradation_level + wear)
        elif operating_state == OperatingState.WARNING:
            wear = (self._wear_rate_per_hour * 2.0 / 3600.0) * time_delta_seconds
            self._hidden_wear_counter += wear
            self._degradation_level = min(100.0, self._degradation_level + wear)
        elif operating_state in (OperatingState.MAINTENANCE, OperatingState.RECOVERY):
            # Partial repair: maintenance reduces degradation at 2% per hour.
            # Simulates physical cleaning, part replacement, and recalibration.
            repair_rate_per_sec = 2.0 / 3600.0  # 2% degradation recovered per hour
            self._degradation_level = max(0.0, self._degradation_level - repair_rate_per_sec * time_delta_seconds)
