"""
FastAPI route handlers for listing and triggering controlled simulation fault scenarios.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_fault_scenario_manager, get_scenario_repository
from api.schemas.scenarios import FaultScenarioItem
from scenarios.manager import FaultScenarioManager
from scenarios.repository import ScenarioStateRepository

router = APIRouter(prefix="/api/scenarios", tags=["Fault Scenarios"])
demo_router = APIRouter(prefix="/api/demo/faults", tags=["Fault Scenarios"])


@router.get("", response_model=List[FaultScenarioItem], summary="List all predefined simulation fault scenarios")
def list_scenarios(
    manager: FaultScenarioManager = Depends(get_fault_scenario_manager),
    repo: ScenarioStateRepository = Depends(get_scenario_repository),
):
    scenarios = manager.list_scenarios()
    active_ids = set(repo.get_active_scenarios())
    result = []
    for s in scenarios:
        d = s.to_dict()
        if s.scenario_id in active_ids:
            d["state"] = "ACTIVE"
        result.append(d)
    return result


@router.get("/active", response_model=List[FaultScenarioItem], summary="List active fault scenarios")
def list_active_scenarios(
    manager: FaultScenarioManager = Depends(get_fault_scenario_manager),
    repo: ScenarioStateRepository = Depends(get_scenario_repository),
):
    active_ids = set(repo.get_active_scenarios())
    scenarios = [s for s in manager.list_scenarios() if s.scenario_id in active_ids]
    result = []
    for s in scenarios:
        d = s.to_dict()
        d["state"] = "ACTIVE"
        result.append(d)
    return result


@router.post("/{scenario_id}/start", response_model=FaultScenarioItem, summary="Start a controlled fault scenario")
@demo_router.post("/{scenario_id}", response_model=FaultScenarioItem, summary="Trigger a demo fault scenario")
def start_scenario(
    scenario_id: str,
    manager: FaultScenarioManager = Depends(get_fault_scenario_manager),
    repo: ScenarioStateRepository = Depends(get_scenario_repository),
):
    scenario = manager.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fault scenario '{scenario_id}' not found.",
        )
    try:
        manager.start_scenario(scenario_id)
    except Exception:
        pass
    repo.set_state(scenario_id=scenario_id, machine_id=scenario.machine_id, state="ACTIVE")
    d = scenario.to_dict()
    d["state"] = "ACTIVE"
    return d


@router.post("/{scenario_id}/stop", response_model=FaultScenarioItem, summary="Stop a controlled fault scenario")
@demo_router.delete("/{scenario_id}", response_model=FaultScenarioItem, summary="Stop a demo fault scenario")
def stop_scenario(
    scenario_id: str,
    manager: FaultScenarioManager = Depends(get_fault_scenario_manager),
    repo: ScenarioStateRepository = Depends(get_scenario_repository),
):
    scenario = manager.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fault scenario '{scenario_id}' not found.",
        )
    try:
        manager.stop_scenario(scenario_id)
    except Exception:
        pass
    repo.set_state(scenario_id=scenario_id, machine_id=scenario.machine_id, state="STOPPED")
    d = scenario.to_dict()
    d["state"] = "RESOLVED"
    return d

