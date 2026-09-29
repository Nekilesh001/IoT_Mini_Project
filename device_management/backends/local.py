"""
Local Backend implementations of DeviceStateBackend, FleetBackend, JobBackend, and AuditBackend.
Uses DeviceManagementRepository (SQLite/PostgreSQL) for local-first operations.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from device_management.backends.base import (
    DeviceStateBackend,
    FleetBackend,
    JobBackend,
    AuditBackend,
)
from device_management.models import (
    ConnectivityState,
    ManagementState,
    JobType,
    JobStatus,
    AuditAction,
    AuditSource,
    DeviceShadowRecord,
    FleetDeviceRecord,
    ManagementJobRecord,
    JobAttemptRecord,
    ManagementAuditRecord,
    FleetSummary,
)
from device_management.repository import DeviceManagementRepository
from device_management.state import DeviceShadowState, VersionConflictError


class LocalDeviceStateBackend(DeviceStateBackend):
    """Local SQLite/Postgres device shadow implementation."""

    def __init__(self, repository: DeviceManagementRepository):
        self._repo = repository

    def get_state(self, device_id: str) -> Optional[DeviceShadowRecord]:
        return self._repo.get_shadow(device_id)

    def update_desired(
        self,
        device_id: str,
        desired_state: Dict[str, Any],
        expected_version: Optional[int] = None,
    ) -> DeviceShadowRecord:
        existing = self._repo.get_shadow(device_id)
        if existing:
            state = DeviceShadowState.from_record(existing)
            state.update_desired(desired_state, expected_version=expected_version)
        else:
            state = DeviceShadowState(
                device_id=device_id,
                desired_state=desired_state,
                version=1,
            )
        return self._repo.upsert_shadow(
            device_id=state.device_id,
            desired_state=state.desired_state,
            reported_state=state.reported_state,
            version=state.version,
        )

    def update_reported(
        self,
        device_id: str,
        reported_state: Dict[str, Any],
    ) -> DeviceShadowRecord:
        existing = self._repo.get_shadow(device_id)
        if existing:
            state = DeviceShadowState.from_record(existing)
            state.update_reported(reported_state)
        else:
            state = DeviceShadowState(
                device_id=device_id,
                reported_state=reported_state,
                version=1,
            )
        return self._repo.upsert_shadow(
            device_id=state.device_id,
            desired_state=state.desired_state,
            reported_state=state.reported_state,
            version=state.version,
        )

    def list_all_states(self) -> List[DeviceShadowRecord]:
        return self._repo.list_all_shadows()


class LocalFleetBackend(FleetBackend):
    """Local SQLite/Postgres fleet metadata and indexing implementation."""

    def __init__(self, repository: DeviceManagementRepository):
        self._repo = repository

    def register_device(self, record: FleetDeviceRecord) -> FleetDeviceRecord:
        return self._repo.register_or_update_device(record)

    def get_device(self, machine_id: str) -> Optional[FleetDeviceRecord]:
        return self._repo.get_device(machine_id)

    def list_devices(
        self,
        connectivity: Optional[ConnectivityState] = None,
        management_state: Optional[ManagementState] = None,
    ) -> List[FleetDeviceRecord]:
        return self._repo.list_devices(connectivity=connectivity, management_state=management_state)

    def update_connectivity(
        self,
        machine_id: str,
        connectivity: ConnectivityState,
    ) -> Optional[FleetDeviceRecord]:
        return self._repo.update_connectivity(machine_id, connectivity)

    def get_summary(self) -> FleetSummary:
        return self._repo.get_fleet_summary()


class LocalJobBackend(JobBackend):
    """Local SQLite/Postgres job engine and attempt history implementation."""

    def __init__(self, repository: DeviceManagementRepository):
        self._repo = repository

    def create_job(self, job: ManagementJobRecord) -> ManagementJobRecord:
        return self._repo.create_job(job)

    def get_job(self, job_id: str) -> Optional[ManagementJobRecord]:
        return self._repo.get_job(job_id)

    def update_job(self, job: ManagementJobRecord) -> ManagementJobRecord:
        return self._repo.update_job(job)

    def list_jobs(
        self,
        machine_id: Optional[str] = None,
        status: Optional[JobStatus] = None,
        limit: int = 100,
    ) -> List[ManagementJobRecord]:
        return self._repo.list_jobs(machine_id=machine_id, status=status, limit=limit)

    def record_attempt(self, attempt: JobAttemptRecord) -> JobAttemptRecord:
        return self._repo.record_attempt(attempt)

    def get_attempts(self, job_id: str) -> List[JobAttemptRecord]:
        return self._repo.get_job_attempts(job_id)


class LocalAuditBackend(AuditBackend):
    """Local SQLite/Postgres audit history implementation."""

    def __init__(self, repository: DeviceManagementRepository):
        self._repo = repository

    def record_event(self, record: ManagementAuditRecord) -> ManagementAuditRecord:
        return self._repo.record_audit(record)

    def list_events(
        self,
        machine_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        limit: int = 100,
    ) -> List[ManagementAuditRecord]:
        return self._repo.list_audit_events(machine_id=machine_id, action=action, limit=limit)
