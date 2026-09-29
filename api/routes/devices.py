"""
FastAPI Route Handlers for Device Registry, Fleet Summary, and Device Shadow State.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from api.dependencies import get_device_management_service
from device_management.service import DeviceManagementService
from device_management.models import (
    ConnectivityState,
    ManagementState,
    DeviceShadowRecord,
    FleetDeviceRecord,
    FleetSummary,
    ManagementJobRecord,
    AuditSource,
)
from device_management.state import VersionConflictError

router = APIRouter(tags=["Device Management & Fleet"])


class PatchShadowRequest(BaseModel):
    desired: Dict[str, Any]
    expected_version: Optional[int] = None
    actor: Optional[AuditSource] = AuditSource.LOCAL_UI


class UpdateDeviceMetadataRequest(BaseModel):
    software_version: Optional[str] = None
    firmware_version: Optional[str] = None
    config_version: Optional[str] = None
    management_state: Optional[ManagementState] = None
    metadata_patch: Optional[Dict[str, Any]] = None


@router.get("/api/devices", response_model=List[FleetDeviceRecord])
def list_devices(
    connectivity: Optional[ConnectivityState] = Query(None, description="Filter by connectivity state"),
    management_state: Optional[ManagementState] = Query(None, description="Filter by management state"),
    service: DeviceManagementService = Depends(get_device_management_service),
):
    """List all registered machines in the factory fleet."""
    return service.fleet.list_machines(
        connectivity=connectivity,
        management_state=management_state,
    )


@router.get("/api/devices/{machine_id}", response_model=FleetDeviceRecord)
def get_device(
    machine_id: str,
    service: DeviceManagementService = Depends(get_device_management_service),
):
    """Retrieve metadata and status for a specific machine."""
    device = service.fleet.get_machine(machine_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{machine_id}' not found in fleet registry.")
    return device


@router.patch("/api/devices/{machine_id}", response_model=FleetDeviceRecord)
def update_device_metadata(
    machine_id: str,
    req: UpdateDeviceMetadataRequest,
    service: DeviceManagementService = Depends(get_device_management_service),
):
    """Update metadata, firmware version, or management state for a machine."""
    updated = service.fleet.update_device_metadata(
        machine_id=machine_id,
        software_version=req.software_version,
        firmware_version=req.firmware_version,
        config_version=req.config_version,
        management_state=req.management_state,
        metadata_patch=req.metadata_patch,
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Device '{machine_id}' not found.")
    return updated


@router.get("/api/devices/{machine_id}/shadow", response_model=DeviceShadowRecord)
def get_device_shadow(
    machine_id: str,
    service: DeviceManagementService = Depends(get_device_management_service),
):
    """Retrieve digital twin shadow state (desired, reported, version, delta)."""
    return service.shadow.get_shadow(machine_id)


@router.patch("/api/devices/{machine_id}/shadow", response_model=DeviceShadowRecord)
def patch_device_shadow_desired(
    machine_id: str,
    req: PatchShadowRequest,
    service: DeviceManagementService = Depends(get_device_management_service),
):
    """Update desired state on the device shadow and increment version."""
    try:
        return service.shadow.update_desired_state(
            device_id=machine_id,
            desired_state=req.desired,
            expected_version=req.expected_version,
            actor=req.actor or AuditSource.LOCAL_UI,
        )
    except VersionConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/api/devices/{machine_id}/shadow/sync", response_model=DeviceShadowRecord)
def sync_device_shadow(
    machine_id: str,
    service: DeviceManagementService = Depends(get_device_management_service),
):
    """Acknowledge synchronization: copies desired state to reported state and clears delta."""
    return service.shadow.sync_reported_from_desired(machine_id, actor=AuditSource.LOCAL_UI)


@router.get("/api/devices/{machine_id}/jobs", response_model=List[ManagementJobRecord])
def list_device_jobs(
    machine_id: str,
    limit: int = Query(50, ge=1, le=200),
    service: DeviceManagementService = Depends(get_device_management_service),
):
    """List management job history for a specific machine."""
    return service.jobs.list_jobs(machine_id=machine_id, limit=limit)


@router.get("/api/fleet/summary", response_model=FleetSummary)
def get_fleet_summary(
    service: DeviceManagementService = Depends(get_device_management_service),
):
    """Get aggregated fleet statistics (online/offline counts, machine types, active jobs)."""
    return service.fleet.get_fleet_summary()
