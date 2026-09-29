"""
Abstract Backend Interfaces for Device State, Fleet Management, Job Execution, and Audit Trails.
Defines clean separation so application logic remains completely agnostic of the underlying infrastructure (Local vs Cloud).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
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


class DeviceStateBackend(ABC):
    """Abstract interface for managing digital twin / shadow state."""

    @abstractmethod
    def get_state(self, device_id: str) -> Optional[DeviceShadowRecord]:
        """Retrieve the current shadow state for a device."""
        pass

    @abstractmethod
    def update_desired(
        self,
        device_id: str,
        desired_state: Dict[str, Any],
        expected_version: Optional[int] = None,
    ) -> DeviceShadowRecord:
        """Update desired state and increment version with optimistic concurrency."""
        pass

    @abstractmethod
    def update_reported(
        self,
        device_id: str,
        reported_state: Dict[str, Any],
    ) -> DeviceShadowRecord:
        """Update reported state received from physical device telemetry or sync."""
        pass

    @abstractmethod
    def list_all_states(self) -> List[DeviceShadowRecord]:
        """List shadow states for all known devices."""
        pass


class FleetBackend(ABC):
    """Abstract interface for fleet registration, indexing, and health tracking."""

    @abstractmethod
    def register_device(self, record: FleetDeviceRecord) -> FleetDeviceRecord:
        """Register a machine in the fleet management registry."""
        pass

    @abstractmethod
    def get_device(self, machine_id: str) -> Optional[FleetDeviceRecord]:
        """Retrieve machine metadata record."""
        pass

    @abstractmethod
    def list_devices(
        self,
        connectivity: Optional[ConnectivityState] = None,
        management_state: Optional[ManagementState] = None,
    ) -> List[FleetDeviceRecord]:
        """Query fleet devices with optional filters."""
        pass

    @abstractmethod
    def update_connectivity(
        self,
        machine_id: str,
        connectivity: ConnectivityState,
    ) -> Optional[FleetDeviceRecord]:
        """Update connectivity status and last seen timestamp."""
        pass

    @abstractmethod
    def get_summary(self) -> FleetSummary:
        """Get aggregated fleet statistics and breakdown."""
        pass


class JobBackend(ABC):
    """Abstract interface for job scheduling, status transitions, retries, and history."""

    @abstractmethod
    def create_job(self, job: ManagementJobRecord) -> ManagementJobRecord:
        """Create and queue a new management job."""
        pass

    @abstractmethod
    def get_job(self, job_id: str) -> Optional[ManagementJobRecord]:
        """Retrieve job details by job_id."""
        pass

    @abstractmethod
    def update_job(self, job: ManagementJobRecord) -> ManagementJobRecord:
        """Update job lifecycle status, error, result, or timestamps."""
        pass

    @abstractmethod
    def list_jobs(
        self,
        machine_id: Optional[str] = None,
        status: Optional[JobStatus] = None,
        limit: int = 100,
    ) -> List[ManagementJobRecord]:
        """Query jobs with optional machine or status filters."""
        pass

    @abstractmethod
    def record_attempt(self, attempt: JobAttemptRecord) -> JobAttemptRecord:
        """Log an execution attempt."""
        pass

    @abstractmethod
    def get_attempts(self, job_id: str) -> List[JobAttemptRecord]:
        """Get all execution attempts for a job."""
        pass


class AuditBackend(ABC):
    """Abstract interface for tracking auditable administrative and system events."""

    @abstractmethod
    def record_event(self, record: ManagementAuditRecord) -> ManagementAuditRecord:
        """Persist an audit log entry."""
        pass

    @abstractmethod
    def list_events(
        self,
        machine_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        limit: int = 100,
    ) -> List[ManagementAuditRecord]:
        """Retrieve audit history filtered by machine or action."""
        pass
