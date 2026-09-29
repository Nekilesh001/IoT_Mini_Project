"""
Global telemetry endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from api.dependencies import get_telemetry_repository, get_factory_profiles
from api.schemas.telemetry import TelemetryRecordItem
from api.services.telemetry_service import TelemetryService

router = APIRouter(prefix="/api/telemetry", tags=["Telemetry"])


@router.get("/latest", response_model=List[TelemetryRecordItem])
def get_all_latest_telemetry(
    machine_id: Optional[str] = Query(None, description="Optional filter by machine ID"),
    repo=Depends(get_telemetry_repository),
    profiles=Depends(get_factory_profiles)
):
    """Retrieve the latest telemetry snapshots across machines."""
    service = TelemetryService(repository=repo, profiles=profiles)
    return service.get_latest_telemetry(machine_id)


@router.get("", response_model=List[TelemetryRecordItem])
def get_telemetry_list(
    machine_id: Optional[str] = Query(None),
    repo=Depends(get_telemetry_repository),
    profiles=Depends(get_factory_profiles)
):
    """Alias for /api/telemetry/latest."""
    return get_all_latest_telemetry(machine_id=machine_id, repo=repo, profiles=profiles)
