"""
Fault Scenario Catalog and Lifecycle Manager.
"""

from typing import Any, Dict, List, Optional, Union
import logging

from simulator.runtime.factory_runtime import FactorySimulator
from scenarios.fault_scenarios import (
    FaultScenario,
    FaultType,
    FaultSeverity,
    FaultLifecycleState,
)

logger = logging.getLogger(__name__)


def create_standard_scenarios() -> Dict[str, FaultScenario]:
    """Generates the standard representative fault scenarios for all machine classes."""
    scenarios = [
        # 1. Pump progressive bearing degradation
        FaultScenario(
            scenario_id="PUMP_BEARING_WEAR",
            machine_id="PMP-001",
            machine_type="INDUSTRIAL_PUMP",
            fault_type=FaultType.MACHINE_FAULT,
            fault_code="PMP-M01",
            title="Pump Bearing Degradation",
            description="Progressive mechanical wear on impeller bearings causing gradual elevation in vibration and motor temperature.",
            severity=FaultSeverity.CRITICAL,
            is_progressive=True,
            target_condition="bearing_wear",
            max_severity_pct=95.0,
        ),
        # 2. Conveyor sudden belt jam
        FaultScenario(
            scenario_id="CONVEYOR_BELT_JAM",
            machine_id="CON-001",
            machine_type="INDUSTRIAL_CONVEYOR",
            fault_type=FaultType.MACHINE_FAULT,
            fault_code="CON-M02",
            title="Conveyor Belt Mechanical Jam",
            description="Sudden material obstruction causing conveyor drive motor stall, sudden drop in belt velocity, and current surge.",
            severity=FaultSeverity.CRITICAL,
            is_progressive=False,
            target_condition="jammed",
            max_severity_pct=100.0,
        ),

        # 3. CNC spindle thermal runaway
        FaultScenario(
            scenario_id="CNC_SPINDLE_OVERHEAT",
            machine_id="CNC-001",
            machine_type="CNC_MACHINING_CENTER",
            fault_type=FaultType.MACHINE_FAULT,
            fault_code="CNC-M01",
            title="CNC Spindle Overtemperature",
            description="Cooling lubrication breakdown leading to high spindle friction, temperature spike, and vibration anomaly.",
            severity=FaultSeverity.WARNING,
            is_progressive=True,
            target_condition="overheating",
            max_severity_pct=85.0,
        ),
        # 4. Chiller low coolant flow
        FaultScenario(
            scenario_id="CHILLER_LOW_FLOW",
            machine_id="CHL-001",
            machine_type="INDUSTRIAL_CHILLER",
            fault_type=FaultType.MACHINE_FAULT,
            fault_code="CHL-M01",
            title="Chiller Flow Restriction",
            description="Refrigeration loop blockage causing low evaporator flow rate and elevated supply fluid temperature.",
            severity=FaultSeverity.WARNING,
            is_progressive=False,
            target_condition="low_flow",
            max_severity_pct=80.0,
        ),
        # 5. AGV battery critical depletion
        FaultScenario(
            scenario_id="AGV_LOW_BATTERY",
            machine_id="AGV-001",
            machine_type="AUTONOMOUS_MOBILE_ROBOT",
            fault_type=FaultType.MACHINE_FAULT,
            fault_code="AGV-M01",
            title="AGV Critical Low Battery",
            description="Battery state-of-charge drops below safe navigation threshold during transport mission.",
            severity=FaultSeverity.WARNING,
            is_progressive=True,
            target_condition="low_battery",
            max_severity_pct=90.0,
        ),
        # 6. Compressor element overheating / filter clog
        FaultScenario(
            scenario_id="COMPRESSOR_FILTER_CLOG",
            machine_id="CMP-001",
            machine_type="AIR_COMPRESSOR",
            fault_type=FaultType.MACHINE_FAULT,
            fault_code="CMP-M01",
            title="Compressor Intake Filter Clog",
            description="Intake filter restriction causing excessive compression ratio, element temperature spike, and pressure instability.",
            severity=FaultSeverity.CRITICAL,
            is_progressive=True,
            target_condition="filter_clog",
            max_severity_pct=90.0,
        ),
        # 7. Robot joint overload
        FaultScenario(
            scenario_id="ROBOT_JOINT_OVERLOAD",
            machine_id="ROB-001",
            machine_type="INDUSTRIAL_ROBOT_6AXIS",
            fault_type=FaultType.MACHINE_FAULT,
            fault_code="ROB-M01",
            title="Robot Joint 1 Overload",
            description="Excessive payload/friction on axis joint motor resulting in high drive current and joint temperature rise.",
            severity=FaultSeverity.WARNING,
            is_progressive=False,
            target_condition="joint_overload",
            max_severity_pct=85.0,
        ),
        # 8. Injection molding cooling failure
        FaultScenario(
            scenario_id="IMM_COOLING_FAILURE",
            machine_id="IMM-001",
            machine_type="INJECTION_MOLDING_MACHINE",
            fault_type=FaultType.MACHINE_FAULT,
            fault_code="IMM-M01",
            title="Injection Mold Cooling Circuit Failure",
            description="Mold zone temperature escalation leading to extended cycle times and thermal warnings.",
            severity=FaultSeverity.WARNING,
            is_progressive=True,
            target_condition="cooling_failure",
            max_severity_pct=75.0,
        ),
        # 9. Industrial press hydraulic pressure drop
        FaultScenario(
            scenario_id="PRESS_PRESSURE_LOSS",
            machine_id="PRS-001",
            machine_type="INDUSTRIAL_PRESS",
            fault_type=FaultType.MACHINE_FAULT,
            fault_code="PRS-M01",
            title="Press Hydraulic Seal Failure",
            description="Hydraulic pressure decay below minimum forming tonnage specification.",
            severity=FaultSeverity.CRITICAL,
            is_progressive=False,
            target_condition="pressure_loss",
            max_severity_pct=90.0,
        ),
        # 10. Vision camera latency and dropout
        FaultScenario(
            scenario_id="VISION_CAMERA_DROPOUT",
            machine_id="VIS-001",
            machine_type="VISION_INSPECTION_STATION",
            fault_type=FaultType.SENSOR_FAULT,
            fault_code="VIS-S01",
            title="Vision Inspection Optical Latency",
            description="Lighting degradation and sensor capture latency exceeding inspection cycle time.",
            severity=FaultSeverity.WARNING,
            is_progressive=False,
            target_condition="sensor_dropout",
            max_severity_pct=70.0,
        ),
    ]
    return {s.scenario_id: s for s in scenarios}


class FaultScenarioManager:
    """
    Coordinates available fault scenarios, injects conditions into FactorySimulator,
    and advances progressive degradation states.
    """

    def __init__(self, factory: Optional[FactorySimulator] = None):
        self._factory = factory
        self._scenarios: Dict[str, FaultScenario] = create_standard_scenarios()

    def set_factory(self, factory: FactorySimulator) -> None:
        self._factory = factory

    def register_scenarios(self, scenarios: Any) -> None:
        if isinstance(scenarios, dict):
            self._scenarios.update(scenarios)
        elif isinstance(scenarios, list):
            for s in scenarios:
                self._scenarios[s.scenario_id] = s

    def register_scenario(self, scenario: FaultScenario) -> None:
        self._scenarios[scenario.scenario_id] = scenario

    def list_scenarios(self) -> List[FaultScenario]:
        return list(self._scenarios.values())

    def get_scenario(self, scenario_id: str) -> Optional[FaultScenario]:
        return self._scenarios.get(scenario_id)

    def start_scenario(self, scenario_id: str) -> FaultScenario:
        """Activates a fault scenario by ID."""
        scenario = self._scenarios.get(scenario_id)
        if not scenario:
            logger.warning(f"Scenario '{scenario_id}' not found.")
            raise KeyError(f"Scenario '{scenario_id}' not found in registry.")

        if not self._factory:
            raise RuntimeError("No FactorySimulator registered with FaultScenarioManager.")

        scenario.start(self._factory)
        logger.info(f"Fault scenario '{scenario_id}' started on machine '{scenario.machine_id}'.")
        return scenario

    def stop_scenario(self, scenario_id: str) -> FaultScenario:
        """Resolves a fault scenario by ID."""
        scenario = self._scenarios.get(scenario_id)
        if not scenario:
            logger.warning(f"Scenario '{scenario_id}' not found.")
            raise KeyError(f"Scenario '{scenario_id}' not found in registry.")

        if scenario.state != FaultLifecycleState.ACTIVE:
            raise KeyError(f"Scenario '{scenario_id}' is not active.")

        if not self._factory:
            raise RuntimeError("No FactorySimulator registered with FaultScenarioManager.")

        scenario.stop(self._factory)
        logger.info(f"Fault scenario '{scenario_id}' stopped on machine '{scenario.machine_id}'.")
        return scenario

    def step(self, dt_seconds: float = 1.0) -> None:
        """Advances all active scenarios with the simulator clock."""
        if not self._factory:
            return
        for scenario in self._scenarios.values():
            if scenario.state == FaultLifecycleState.ACTIVE:
                scenario.advance(self._factory, dt_seconds=dt_seconds)

    def advance_scenarios(self, dt_seconds: float = 1.0) -> None:
        self.step(dt_seconds=dt_seconds)

    def get_active_scenarios(self) -> Dict[str, FaultScenario]:
        return {s.scenario_id: s for s in self._scenarios.values() if s.state == FaultLifecycleState.ACTIVE}

