"""
FastAPI Routes for Edge ML Inference, Anomaly Monitoring, and Predictive Maintenance.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from api.dependencies import get_ml_repository, get_ml_service

router = APIRouter(prefix="/api/ml", tags=["Machine Learning"])


@router.get("/status")
def get_ml_system_status(
    service=Depends(get_ml_service),
    repo=Depends(get_ml_repository),
) -> Dict[str, Any]:
    """
    Returns overarching health, runtime backend, and configuration status of the ML subsystem.
    """
    status_data = service.get_status()
    fleet_summary = repo.get_fleet_summary()
    status_data["fleet_summary"] = fleet_summary
    return status_data


@router.get("/models")
def list_ml_models(service=Depends(get_ml_service)) -> List[Dict[str, Any]]:
    """
    Returns list of loaded machine learning model bundles and their metadata.
    """
    return service.get_models()


@router.get("/metrics")
def get_ml_metrics(service=Depends(get_ml_service)) -> Dict[str, Any]:
    """
    Returns live inference latency percentiles and performance benchmarks.
    """
    return service.metrics_tracker.get_summary()


@router.get("/fleet-summary")
def get_fleet_ml_summary(repo=Depends(get_ml_repository)) -> Dict[str, Any]:
    """
    Returns fleet-wide anomaly and RUL indicators across all monitored machines.
    """
    return repo.get_fleet_summary()


@router.get("/machines/{machine_id}")
def get_machine_latest_inference(
    machine_id: str,
    service=Depends(get_ml_service),
    repo=Depends(get_ml_repository),
) -> Dict[str, Any]:
    """
    Returns the latest ML inference result (anomaly score and predicted RUL) for a machine.
    """
    # Check in-memory service first
    latest = service.get_latest_inference(machine_id)
    if latest:
        return latest.to_dict()

    # Fallback to database
    db_rec = repo.get_latest_by_machine(machine_id)
    if db_rec:
        return db_rec.to_dict()

    raise HTTPException(
        status_code=404,
        detail=f"No ML inference results found for machine '{machine_id}'"
    )


@router.get("/inferences")
def list_ml_inferences(
    machine_id: Optional[str] = Query(None, description="Filter by machine ID"),
    limit: int = Query(50, ge=1, le=500, description="Max records to return"),
    repo=Depends(get_ml_repository),
) -> List[Dict[str, Any]]:
    """
    Queries historical ML inference predictions.
    """
    if machine_id:
        records = repo.get_history(machine_id=machine_id, limit=limit)
    else:
        records = repo.list_recent(limit=limit)

    return [r.to_dict() for r in records]
