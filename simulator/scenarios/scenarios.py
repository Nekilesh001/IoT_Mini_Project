"""
Deterministic simulation scenarios for testing causal telemetry and fault injection hooks.
"""

from typing import List
from simulator.core.domain import TelemetrySnapshot
from simulator.runtime.factory_runtime import FactorySimulator


class BaseScenario:
    def __init__(self, simulator: FactorySimulator, seed: int = 42):
        self.simulator = simulator
        self.seed = seed
        self.simulator.set_seed(seed)

    def execute(self, ticks: int = 10) -> List[List[TelemetrySnapshot]]:
        raise NotImplementedError


class NormalOperationScenario(BaseScenario):
    """Simulates healthy normal operation across all 12 factory machines."""
    def execute(self, ticks: int = 10) -> List[List[TelemetrySnapshot]]:
        self.simulator.start()
        return self.simulator.run(ticks=ticks)


class BearingDegradationScenario(BaseScenario):
    """
    Simulates progressive bearing degradation on pump PMP-001,
    demonstrating causal increases in vibration and bearing temperature.
    """
    def execute(self, ticks: int = 20) -> List[List[TelemetrySnapshot]]:
        self.simulator.start()
        pump = self.simulator.get_machine("PMP-001")
        pump.set_scenario_id("BEARING_DEGRADATION")

        history = []
        for i in range(ticks):
            if i >= 5:
                # Progressive degradation increase
                deg = min(90.0, (i - 5) * 5.0)
                pump.set_degradation(deg)
                pump.apply_condition("bearing_wear", severity=deg)
            self.simulator.step()
            history.append(self.simulator.collect_telemetry())
        return history


class OverheatingFaultScenario(BaseScenario):
    """
    Simulates filter clog and thermal buildup on compressor CMP-001,
    causing element temperature spike and alarm state transition.
    """
    def execute(self, ticks: int = 15) -> List[List[TelemetrySnapshot]]:
        self.simulator.start()
        comp = self.simulator.get_machine("CMP-001")
        comp.set_scenario_id("OVERHEATING_FAULT")

        history = []
        for i in range(ticks):
            if i == 5:
                comp.apply_condition("filter_clog", severity=75.0)
            self.simulator.step()
            history.append(self.simulator.collect_telemetry())
        return history
