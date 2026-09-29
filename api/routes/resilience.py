"""
FastAPI Routes for Component Resilience, Failure Injection Catalog, and Test Results.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from failure_testing.models import FailureScenarioType, FailureTarget, ScenarioResult
from failure_testing.scenarios import SCENARIO_DEFINITIONS
from failure_testing.runner import FailureTestRunner
from security.authorization import get_current_user, require_permission
from security.models import Permission, User

router = APIRouter(tags=["Resilience & Failure Testing"])

_latest_results: List[ScenarioResult] = []


class ResilienceStatusResponse(BaseModel):
    event_bus: str
    primary_database: str
    ml_inference: str
    alert_engine: str
    protocol_adapters: str
    buffer_queue: str
    active_injected_faults: List[str]
    last_recovery_timestamp: Optional[str]


class RunScenarioRequest(BaseModel):
    scenario_type: Optional[FailureScenarioType] = None


@router.get("/api/resilience/status", response_model=ResilienceStatusResponse)
def get_resilience_status():
    """Get real-time operational health across factory communication and data pipelines."""
    from failure_testing.injector import get_failure_injector
    injector = get_failure_injector()
    active_faults = [f.name for f in injector.get_active_faults()]

    return ResilienceStatusResponse(
        event_bus="DEGRADED" if FailureScenarioType.MQTT_OUTAGE.value in active_faults else "HEALTHY",
        primary_database="UNAVAILABLE" if FailureScenarioType.DATABASE_OUTAGE.value in active_faults else "HEALTHY",
        ml_inference="DEGRADED" if FailureScenarioType.ML_INFERENCE_FAILURE.value in active_faults or FailureScenarioType.ML_MODEL_LOAD_FAILURE.value in active_faults else "HEALTHY",
        alert_engine="DEGRADED" if FailureScenarioType.ALERT_PERSISTENCE_FAILURE.value in active_faults else "HEALTHY",
        protocol_adapters="DEGRADED" if FailureScenarioType.PROTOCOL_FAILURE.value in active_faults else "HEALTHY",
        buffer_queue="ACTIVE",
        active_injected_faults=active_faults,
        last_recovery_timestamp=None,
    )


@router.get("/api/resilience/scenarios", response_model=List[Dict[str, Any]])
def list_failure_scenarios():
    """Return catalog of defined deterministic failure and recovery injection scenarios."""
    scenarios = []
    for sc_type, meta in SCENARIO_DEFINITIONS.items():
        scenarios.append({
            "scenario_type": sc_type.value,
            "target_component": meta["target"].value,
            "description": meta["description"],
            "expected_behavior": meta["expected"],
        })
    return scenarios


@router.post("/api/resilience/run", response_model=List[Dict[str, Any]])
def execute_resilience_tests(
    req: RunScenarioRequest = RunScenarioRequest(),
    current_user: User = Depends(require_permission(Permission.INJECT_FAULT_SCENARIOS)),
):
    """
    Execute controlled local failure injection scenarios and verify recovery invariants.
    Requires MAINTAINER or ADMIN role.
    """
    global _latest_results
    runner = FailureTestRunner()

    if req.scenario_type:
        method_map = {
            FailureScenarioType.MQTT_OUTAGE: runner.test_mqtt_outage,
            FailureScenarioType.DATABASE_OUTAGE: runner.test_database_outage,
            FailureScenarioType.PROTOCOL_FAILURE: runner.test_protocol_failure,
            FailureScenarioType.INVALID_TELEMETRY: runner.test_telemetry_corruption,
            FailureScenarioType.ML_MODEL_LOAD_FAILURE: runner.test_ml_failure,
            FailureScenarioType.ALERT_PERSISTENCE_FAILURE: runner.test_alert_persistence_failure,
            FailureScenarioType.DEVICE_JOB_FAILURE: runner.test_job_retry_failure,
            FailureScenarioType.SERVICE_RESTART_RECOVERY: runner.test_restart_recovery,
        }
        test_fn = method_map.get(req.scenario_type)
        if not test_fn:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Individual test execution not implemented for scenario '{req.scenario_type}'.",
            )
        results = [test_fn()]
    else:
        results = runner.run_all_scenarios()

    _latest_results = results
    return [r.to_dict() for r in results]


@router.get("/api/resilience/results", response_model=List[Dict[str, Any]])
def get_latest_resilience_results():
    """Retrieve results and recovery metrics from the most recent failure test execution."""
    global _latest_results
    if not _latest_results:
        # Run default suite if empty
        runner = FailureTestRunner()
        _latest_results = runner.run_all_scenarios()
    return [r.to_dict() for r in _latest_results]
