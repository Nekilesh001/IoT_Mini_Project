"""
Device Management Domain Models, Enums, and Schemas.
Local-first representation of Device Shadow, Fleet Devices, Jobs, Attempts, and Audit logs.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ConnectivityState(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    DEGRADED = "DEGRADED"
    UNKNOWN = "UNKNOWN"


class ManagementState(str, Enum):
    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    UNPROVISIONED = "UNPROVISIONED"
    QUARANTINED = "QUARANTINED"
    DECOMMISSIONED = "DECOMMISSIONED"


class JobType(str, Enum):
    CONFIG_UPDATE = "CONFIG_UPDATE"
    COMMAND = "COMMAND"
    OTA_SIMULATION = "OTA_SIMULATION"
    RESTART_SIMULATION = "RESTART_SIMULATION"
    SYNC_STATE = "SYNC_STATE"


class JobStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class CommandType(str, Enum):
    SET_MODE = "SET_MODE"
    SET_SAMPLING_INTERVAL = "SET_SAMPLING_INTERVAL"
    REQUEST_STATE_SYNC = "REQUEST_STATE_SYNC"
    SIMULATE_RESTART = "SIMULATE_RESTART"
    CUSTOM = "CUSTOM"


class AuditSource(str, Enum):
    LOCAL_UI = "LOCAL_UI"
    LOCAL_SERVICE = "LOCAL_SERVICE"
    SYSTEM = "SYSTEM"
    CLI = "CLI"
    TEST = "TEST"


class AuditAction(str, Enum):
    SHADOW_DESIRED_UPDATED = "SHADOW_DESIRED_UPDATED"
    SHADOW_REPORTED_UPDATED = "SHADOW_REPORTED_UPDATED"
    SHADOW_SYNCED = "SHADOW_SYNCED"
    DEVICE_REGISTERED = "DEVICE_REGISTERED"
    DEVICE_UPDATED = "DEVICE_UPDATED"
    CONNECTIVITY_CHANGED = "CONNECTIVITY_CHANGED"
    JOB_CREATED = "JOB_CREATED"
    JOB_STARTED = "JOB_STARTED"
    JOB_COMPLETED = "JOB_COMPLETED"
    JOB_FAILED = "JOB_FAILED"
    JOB_RETRIED = "JOB_RETRIED"
    JOB_CANCELLED = "JOB_CANCELLED"
    COMMAND_EXECUTED = "COMMAND_EXECUTED"


class DeviceShadowRecord(BaseModel):
    """Local representation of a device's twin / shadow state."""
    device_id: str
    desired_state: Dict[str, Any] = Field(default_factory=dict)
    reported_state: Dict[str, Any] = Field(default_factory=dict)
    delta: Dict[str, Any] = Field(default_factory=dict)
    version: int = 1
    is_sync_pending: bool = False
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FleetDeviceRecord(BaseModel):
    """Local metadata record for a managed machine in the fleet."""
    machine_id: str
    machine_type: str
    protocol: str
    connectivity: ConnectivityState = ConnectivityState.UNKNOWN
    management_state: ManagementState = ManagementState.ACTIVE
    software_version: str = "1.0.0"
    firmware_version: str = "v1.0.0"
    config_version: str = "1.0.0"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    last_seen: Optional[datetime] = None
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ManagementJobRecord(BaseModel):
    """Local representation of a device job (configuration rollout, OTA simulation, command)."""
    job_id: str
    machine_id: str
    job_type: JobType
    payload: Dict[str, Any] = Field(default_factory=dict)
    status: JobStatus = JobStatus.PENDING
    attempt: int = 0
    max_attempts: int = 3
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class JobAttemptRecord(BaseModel):
    """Historical record of an individual execution attempt for a job."""
    attempt_id: str
    job_id: str
    attempt_number: int
    status: JobStatus
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


class ManagementAuditRecord(BaseModel):
    """Auditable log entry for every state change or administrative action."""
    event_id: str
    machine_id: str
    action: AuditAction
    actor: AuditSource = AuditSource.LOCAL_SERVICE
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class FleetSummary(BaseModel):
    """Aggregated fleet management metrics."""
    total_machines: int = 0
    online_count: int = 0
    offline_count: int = 0
    degraded_count: int = 0
    active_jobs_count: int = 0
    pending_sync_count: int = 0
    machines_by_type: Dict[str, int] = Field(default_factory=dict)
    machines_by_protocol: Dict[str, int] = Field(default_factory=dict)
