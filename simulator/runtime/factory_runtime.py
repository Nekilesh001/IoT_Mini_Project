"""
Factory Simulator runtime managing the 12 heterogeneous machines.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from simulator.core.domain import MachineProfile, OperatingState, TelemetrySnapshot
from simulator.core.machine import BaseMachine


class FactorySimulator:
    """
    Factory Simulator managing lifecycle, simulation execution, and telemetry collection
    for all 12 heterogeneous factory machines.
    """

    def __init__(self, config_file: Optional[str] = None, seed: Optional[int] = None):
        self._machines: Dict[str, BaseMachine] = {}
        self._seed: Optional[int] = seed
        self._config_file: Path = Path(config_file) if config_file else Path(__file__).parent.parent / "config" / "machines.json"
        self._is_running: bool = False
        self._total_ticks: int = 0
        self.initialize()

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def total_ticks(self) -> int:
        return self._total_ticks

    def initialize(self) -> None:
        """Load machine definitions from configuration and instantiate all 12 machines."""
        if not self._config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {self._config_file}")

        with open(self._config_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        plant_id = data.get("plant_id", "PLANT_01")
        line_id = data.get("line_id", "LINE_A")
        machines_data = data.get("machines", [])

        self._machines.clear()
        for i, m_data in enumerate(machines_data):
            profile = MachineProfile.from_dict(m_data, plant_id=plant_id, line_id=line_id)
            machine_seed = (self._seed + i * 100) if self._seed is not None else None
            machine = BaseMachine(profile=profile, seed=machine_seed)
            self._machines[machine.machine_id] = machine

    def set_seed(self, seed: Optional[int]) -> None:
        self._seed = seed
        for i, (m_id, machine) in enumerate(self._machines.items()):
            machine_seed = (seed + i * 100) if seed is not None else None
            machine.set_seed(machine_seed)

    def start(self) -> None:
        """Start all machines (OFF -> STARTING -> IDLE -> RUNNING)."""
        for machine in self._machines.values():
            if machine.operating_state == OperatingState.OFF:
                machine.set_operating_state(OperatingState.STARTING)
                machine.set_operating_state(OperatingState.IDLE)
                machine.set_operating_state(OperatingState.RUNNING)
        self._is_running = True

    def stop(self) -> None:
        """Stop all machines (RUNNING/IDLE -> OFF)."""
        for machine in self._machines.values():
            if machine.operating_state in (OperatingState.RUNNING, OperatingState.IDLE, OperatingState.WARNING):
                machine.set_operating_state(OperatingState.IDLE)
                machine.set_operating_state(OperatingState.OFF)
            elif machine.operating_state != OperatingState.OFF:
                machine.force_operating_state(OperatingState.OFF)
        self._is_running = False

    def step(self, time_delta_seconds: float = 1.0) -> None:
        """Advance simulation clock by time_delta_seconds for all 12 machines."""
        self._total_ticks += 1
        for machine in self._machines.values():
            machine.step(time_delta_seconds)

    def run(self, ticks: int, time_delta_seconds: float = 1.0) -> List[List[TelemetrySnapshot]]:
        """
        Run simulation deterministically for a specified number of ticks and return telemetry history.
        """
        history = []
        if not self._is_running:
            self.start()

        for _ in range(ticks):
            self.step(time_delta_seconds)
            history.append(self.collect_telemetry())
        return history

    def get_machine(self, machine_id: str) -> BaseMachine:
        """Retrieve machine instance by machine ID."""
        if machine_id not in self._machines:
            raise KeyError(f"Machine '{machine_id}' not found in factory catalog.")
        return self._machines[machine_id]

    def get_all_machines(self) -> List[BaseMachine]:
        """Return list of all 12 machine instances."""
        return list(self._machines.values())

    def collect_telemetry(self) -> List[TelemetrySnapshot]:
        """Collect current telemetry snapshots from all 12 machines."""
        return [machine.generate_snapshot() for machine in self._machines.values()]
