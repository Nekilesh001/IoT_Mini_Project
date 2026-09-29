"""
Machine metadata, overview, and machine-specific telemetry routes.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from api.dependencies import get_telemetry_repository, get_factory_profiles, get_api_config
from api.schemas.machine import MachineOverviewItem, MachineDetailResponse
from api.schemas.telemetry import TelemetryRecordItem, TelemetryHistoryResponse
from api.services.factory_service import FactoryService
from api.services.telemetry_service import TelemetryService

router = APIRouter(prefix="/api/machines", tags=["Machines"])


@router.get("", response_model=List[MachineOverviewItem])
def list_machines(
    repo=Depends(get_telemetry_repository),
    profiles=Depends(get_factory_profiles)
):
    """List all 12 machines with their latest operating status and key measurements."""
    service = FactoryService(repository=repo, profiles=profiles)
    return service.get_all_machines()


@router.get("/{machine_id}", response_model=MachineDetailResponse)
def get_machine_detail(
    machine_id: str,
    repo=Depends(get_telemetry_repository),
    profiles=Depends(get_factory_profiles)
):
    """Detailed specifications, signal catalog, and current status for a machine."""
    service = FactoryService(repository=repo, profiles=profiles)
    detail = service.get_machine_detail(machine_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Machine '{machine_id}' not found in factory catalog")
    return detail


@router.get("/{machine_id}/latest", response_model=TelemetryRecordItem)
def get_machine_latest_telemetry(
    machine_id: str,
    repo=Depends(get_telemetry_repository),
    profiles=Depends(get_factory_profiles)
):
    """Get the most recent canonical telemetry record for a machine."""
    if machine_id not in profiles:
        raise HTTPException(status_code=404, detail=f"Machine '{machine_id}' not found")
    service = TelemetryService(repository=repo, profiles=profiles)
    records = service.get_latest_telemetry(machine_id)
    if not records:
        raise HTTPException(status_code=404, detail=f"No telemetry records found for machine '{machine_id}'")
    return records[0]


@router.get("/{machine_id}/history", response_model=TelemetryHistoryResponse)
def get_machine_history(
    machine_id: str,
    start: Optional[datetime] = Query(None, description="Start timestamp in ISO 8601 format"),
    end: Optional[datetime] = Query(None, description="End timestamp in ISO 8601 format"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of records"),
    signals: Optional[str] = Query(None, description="Comma-separated list of signals to include"),
    repo=Depends(get_telemetry_repository),
    profiles=Depends(get_factory_profiles)
):
    """Query time-range history for a machine's sensor telemetry."""
    if machine_id not in profiles:
        raise HTTPException(status_code=404, detail=f"Machine '{machine_id}' not found")

    if start and end and start > end:
        raise HTTPException(status_code=400, detail="Start timestamp must be before end timestamp")

    signal_list = [s.strip() for s in signals.split(",") if s.strip()] if signals else None
    service = TelemetryService(repository=repo, profiles=profiles)
    return service.get_machine_history(
        machine_id=machine_id,
        start_time=start,
        end_time=end,
        limit=limit,
        signals=signal_list
    )


@router.get("/{machine_id}/telemetry", response_model=TelemetryHistoryResponse)
def get_machine_telemetry_alias(
    machine_id: str,
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    signals: Optional[str] = Query(None),
    repo=Depends(get_telemetry_repository),
    profiles=Depends(get_factory_profiles)
):
    """Alias for /api/machines/{machine_id}/history."""
    return get_machine_history(
        machine_id=machine_id,
        start=start,
        end=end,
        limit=limit,
        signals=signals,
        repo=repo,
        profiles=profiles
    )
