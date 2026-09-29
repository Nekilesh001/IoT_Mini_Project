"""
FastAPI Route Handlers for Management Jobs, Command Dispatch, and Audit Trails.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from api.dependencies import get_device_management_service
from device_management.service import DeviceManagementService
from device_management.models import (
    JobType,
    JobStatus,
    CommandType,
    AuditAction,
    AuditSource,
    ManagementJobRecord,
    JobAttemptRecord,
    ManagementAuditRecord,
)
from device_management.jobs import InvalidJobStateTransitionError
from device_management.commands import CommandValidationError

router = APIRouter(tags=["Management Jobs & Audit"])


class CreateJobRequest(BaseModel):
    machine_id: str
    job_type: JobType
    payload: Dict[str, Any] = Field(default_factory=dict)
    max_attempts: int = Field(default=3, ge=1, le=10)
    actor: Optional[AuditSource] = AuditSource.LOCAL_UI


class ExecuteCommandRequest(BaseModel):
    machine_id: str
    command_type: CommandType
    payload: Dict[str, Any] = Field(default_factory=dict)
    as_job: bool = True
    actor: Optional[AuditSource] = AuditSource.LOCAL_UI


class CancelJobRequest(BaseModel):
    reason: Optional[str] = "Cancelled by user"
    actor: Optional[AuditSource] = AuditSource.LOCAL_UI


class ExecuteJobRequest(BaseModel):
    simulate_failure: bool = False
    failure_error: Optional[str] = "Simulated execution error"


@router.get("/api/jobs", response_model=List[ManagementJobRecord])
def list_jobs(
    machine_id: Optional[str] = Query(None, description="Filter by target machine"),
    status: Optional[JobStatus] = Query(None, description="Filter by job status"),
    limit: int = Query(100, ge=1, le=500),
    service: DeviceManagementService = Depends(get_device_management_service),
):
    """List management jobs across the factory with optional filters."""
    return service.jobs.list_jobs(machine_id=machine_id, status=status, limit=limit)


@router.post("/api/jobs", response_model=ManagementJobRecord, status_code=status.HTTP_201_CREATED)
def create_job(
    req: CreateJobRequest,
    service: DeviceManagementService = Depends(get_device_management_service),
):
    """Create and queue a new management job (CONFIG_UPDATE, OTA_SIMULATION, COMMAND, etc.)."""
    return service.jobs.create_job(
        machine_id=req.machine_id,
        job_type=req.job_type,
        payload=req.payload,
        max_attempts=req.max_attempts,
        actor=req.actor or AuditSource.LOCAL_UI,
    )


@router.post("/api/commands/execute")
def execute_command(
    req: ExecuteCommandRequest,
    service: DeviceManagementService = Depends(get_device_management_service),
):
    """Validate and execute an administrative machine command."""
    try:
        job_record, result = service.commands.execute_command(
            machine_id=req.machine_id,
            command_type=req.command_type,
            payload=req.payload,
            actor=req.actor or AuditSource.LOCAL_UI,
            as_job=req.as_job,
        )
        return {
            "result": result,
            "job": job_record.model_dump(mode="json") if job_record else None,
        }
    except CommandValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/jobs/{job_id}", response_model=ManagementJobRecord)
def get_job(
    job_id: str,
    service: DeviceManagementService = Depends(get_device_management_service),
):
    """Retrieve details and status for a specific job."""
    job = service.jobs.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return job


@router.post("/api/jobs/{job_id}/execute", response_model=ManagementJobRecord)
def execute_job_locally(
    job_id: str,
    req: Optional[ExecuteJobRequest] = None,
    service: DeviceManagementService = Depends(get_device_management_service),
):
    """Run a queued job through its local execution lifecycle."""
    try:
        sim_fail = req.simulate_failure if req else False
        fail_err = req.failure_error if req and req.failure_error else "Simulated execution error"
        return service.execute_job_locally(
            job_id=job_id,
            simulate_failure=sim_fail,
            failure_error=fail_err,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidJobStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/jobs/{job_id}/cancel", response_model=ManagementJobRecord)
def cancel_job(
    job_id: str,
    req: Optional[CancelJobRequest] = None,
    service: DeviceManagementService = Depends(get_device_management_service),
):
    """Cancel a pending or running job."""
    try:
        reason = req.reason if req else "Cancelled by user"
        actor = req.actor if req and req.actor else AuditSource.LOCAL_UI
        return service.jobs.cancel_job(job_id=job_id, reason=reason, actor=actor)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidJobStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/jobs/{job_id}/attempts", response_model=List[JobAttemptRecord])
def get_job_attempts(
    job_id: str,
    service: DeviceManagementService = Depends(get_device_management_service),
):
    """Retrieve all execution and retry attempts for a job."""
    return service.jobs.get_job_attempts(job_id)


@router.get("/api/management/audit", response_model=List[ManagementAuditRecord])
def get_management_audit_trail(
    machine_id: Optional[str] = Query(None, description="Filter audit events by machine ID"),
    action: Optional[AuditAction] = Query(None, description="Filter audit events by action"),
    limit: int = Query(100, ge=1, le=500),
    service: DeviceManagementService = Depends(get_device_management_service),
):
    """Retrieve chronological audit trail of all management and shadow actions."""
    return service.get_audit_trail(machine_id=machine_id, action=action, limit=limit)
