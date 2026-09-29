"""
Device Management Module.
Local-first Device Shadow, Fleet Management, Job Execution Engine, and AWS-Ready Adapter Scaffolds.
"""

from device_management.models import (
    ConnectivityState,
    ManagementState,
    JobType,
    JobStatus,
    CommandType,
    AuditSource,
    AuditAction,
    DeviceShadowRecord,
    FleetDeviceRecord,
    ManagementJobRecord,
    JobAttemptRecord,
    ManagementAuditRecord,
    FleetSummary,
)
from device_management.state import DeviceShadowState, VersionConflictError
from device_management.shadow import DeviceShadowManager
from device_management.fleet import FleetManager
from device_management.jobs import JobManager, InvalidJobStateTransitionError
from device_management.commands import CommandHandler, CommandValidationError
from device_management.repository import (
    DeviceManagementRepository,
    DeviceShadowModel,
    FleetDeviceModel,
    ManagementJobModel,
    JobAttemptModel,
    ManagementAuditModel,
)
from device_management.service import DeviceManagementService
from device_management.backends import (
    DeviceStateBackend,
    FleetBackend,
    JobBackend,
    AuditBackend,
    LocalDeviceStateBackend,
    LocalFleetBackend,
    LocalJobBackend,
    LocalAuditBackend,
)

__all__ = [
    "ConnectivityState",
    "ManagementState",
    "JobType",
    "JobStatus",
    "CommandType",
    "AuditSource",
    "AuditAction",
    "DeviceShadowRecord",
    "FleetDeviceRecord",
    "ManagementJobRecord",
    "JobAttemptRecord",
    "ManagementAuditRecord",
    "FleetSummary",
    "DeviceShadowState",
    "VersionConflictError",
    "DeviceShadowManager",
    "FleetManager",
    "JobManager",
    "InvalidJobStateTransitionError",
    "CommandHandler",
    "CommandValidationError",
    "DeviceManagementRepository",
    "DeviceShadowModel",
    "FleetDeviceModel",
    "ManagementJobModel",
    "JobAttemptModel",
    "ManagementAuditModel",
    "DeviceManagementService",
    "DeviceStateBackend",
    "FleetBackend",
    "JobBackend",
    "AuditBackend",
    "LocalDeviceStateBackend",
    "LocalFleetBackend",
    "LocalJobBackend",
    "LocalAuditBackend",
]
