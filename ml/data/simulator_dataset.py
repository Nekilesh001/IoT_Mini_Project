"""
Deterministic simulator dataset generator for comprehensive offline ML training.

Reuses the existing FactorySimulator and FaultScenarioManager to produce
high-fidelity, heterogeneous multi-machine time-series telemetry with known offline targets.
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from simulator.runtime.factory_runtime import FactorySimulator
from scenarios.manager import FaultScenarioManager, create_standard_scenarios
from ml.data.collectors import BaseTelemetryCollector
from ml.data.labels import compute_ground_truth_labels


class SimulatorDatasetGenerator(BaseTelemetryCollector):
    """
    Generates deterministic, temporal multi-machine datasets simulating healthy cycles,
    progressive degradation, intermittent faults, varying operating loads, and recovery.
    """

    def __init__(self, seed: int = 42, base_time: Optional[datetime] = None):
        self._seed = seed
        self._base_time = base_time or datetime(2026, 1, 1, 8, 0, 0, tzinfo=timezone.utc)

    def collect(
        self,
        num_ticks: int = 600,
        dt_seconds: float = 1.0,
        inject_scenarios: bool = True,
        **kwargs
    ) -> pd.DataFrame:
        """
        Executes a deterministic factory simulation run over `num_ticks` steps.
        """
        factory = FactorySimulator(seed=self._seed)
        scenario_mgr = FaultScenarioManager(factory=factory)
        factory.start()

        records: List[Dict[str, Any]] = []
        current_time = self._base_time

        # Schedule scenario injection windows across time
        # E.g. Phase 1 (0 to 150): Healthy Baseline
        # E.g. Phase 2 (150 to 350): Progressive Degradation on subset of machines
        # E.g. Phase 3 (350 to 450): Sudden Faults
        # E.g. Phase 4 (450 to 600): Maintenance / Recovery & Post-recovery healthy
        all_scenarios = list(scenario_mgr.list_scenarios())

        active_injections: Dict[int, str] = {}
        stop_injections: Dict[int, str] = {}

        if inject_scenarios and all_scenarios:
            # Spread 4 distinct scenarios across time
            if len(all_scenarios) >= 4:
                active_injections[120] = all_scenarios[0].scenario_id  # PUMP_BEARING_WEAR
                stop_injections[400] = all_scenarios[0].scenario_id

                active_injections[200] = all_scenarios[2].scenario_id  # CNC_SPINDLE_OVERHEAT
                stop_injections[420] = all_scenarios[2].scenario_id

                active_injections[280] = all_scenarios[1].scenario_id  # CONVEYOR_BELT_JAM
                stop_injections[380] = all_scenarios[1].scenario_id

                active_injections[320] = all_scenarios[4].scenario_id  # AGV_LOW_BATTERY
                stop_injections[450] = all_scenarios[4].scenario_id

        for tick in range(1, num_ticks + 1):
            # Check for scheduled scenario start/stop
            if tick in active_injections:
                scen_id = active_injections[tick]
                try:
                    scenario_mgr.start_scenario(scen_id)
                except Exception:
                    pass

            if tick in stop_injections:
                scen_id = stop_injections[tick]
                try:
                    scenario_mgr.stop_scenario(scen_id)
                except Exception:
                    pass

            # Advance scenario states and factory simulation physics
            scenario_mgr.step(dt_seconds=dt_seconds)
            factory.step(time_delta_seconds=dt_seconds)

            current_time += timedelta(seconds=dt_seconds)

            # Collect telemetry snapshots from all 12 machines
            snapshots = factory.collect_telemetry()

            for snap in snapshots:
                machine = factory.get_machine(snap.machine_id)
                deg_pct = machine._degradation.degradation_level if machine else 0.0
                active_conds = machine._degradation.active_conditions if machine else {}

                plant_id = machine.profile.plant_id if machine else "PLANT_01"
                line_id = machine.profile.line_id if machine else "LINE_A"

                row: Dict[str, Any] = {
                    "event_id": f"SIM-{snap.machine_id}-{tick:06d}",
                    "machine_id": snap.machine_id,
                    "machine_type": str(snap.machine_type),
                    "plant_id": plant_id,
                    "line_id": line_id,
                    "protocol": str(snap.protocol_metadata),
                    "event_time": current_time.isoformat(),
                    "sequence": tick,
                    "operating_state": str(snap.operating_state),
                    "health_state": str(snap.health_state),
                    "quality": "GOOD",
                    # Simulator internal ground-truth variables (prefixed with sim_ for label calculation only)
                    "sim_degradation_pct": deg_pct,
                    "sim_active_conditions_count": len(active_conds),
                    "sim_is_fault": 1 if (len(active_conds) > 0 or deg_pct >= 50.0) else 0,
                }

                # Flatten observable physical measurements
                if isinstance(snap.public_measurements, dict):
                    row.update(snap.public_measurements)

                records.append(row)

        df = pd.DataFrame(records)
        df["event_time"] = pd.to_datetime(df["event_time"])
        df = df.sort_values(["machine_id", "event_time"]).reset_index(drop=True)

        # Compute ground truth targets
        df_with_targets = compute_ground_truth_labels(df)
        return df_with_targets
