"""
Device Management Service.
Central orchestrator facade coordinating Device Shadow, Fleet Management, Jobs, Commands, and Audit logs.
"""

from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional, Tuple

from simulator.core.domain import MachineProfile
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
from device_management.shadow import DeviceShadowManager
from device_management.fleet import FleetManager
from device_management.jobs import JobManager
from device_management.commands import CommandHandler


class DeviceManagementService:
    """
    Main application service facade for local-first device and fleet management.
    """

    def __init__(
        self,
        state_backend: DeviceStateBackend,
        fleet_backend: FleetBackend,
        job_backend: JobBackend,
        audit_backend: AuditBackend,
    ):
        self._state_backend = state_backend
        self._fleet_backend = fleet_backend
        self._job_backend = job_backend
        self._audit_backend = audit_backend

        self.shadow = DeviceShadowManager(state_backend, audit_backend)
        self.fleet = FleetManager(fleet_backend, audit_backend)
        self.jobs = JobManager(job_backend, audit_backend)
        self.commands = CommandHandler(self.shadow, self.jobs, audit_backend)

    # -------------------------------------------------------------------------
    # Fleet & Shadow Helpers
    # -------------------------------------------------------------------------
    def bootstrap_fleet(self, profiles: Dict[str, MachineProfile]) -> List[FleetDeviceRecord]:
        """Bootstrap fleet records and initial shadow states for factory machines."""
        records = self.fleet.register_all_from_profiles(profiles)
        for machine_id, profile in profiles.items():
            # Initial shadow
            existing_shadow = self.shadow.get_shadow(machine_id)
            if not existing_shadow.reported_state:
                hz = getattr(profile, "nominal_sampling_rate_hz", 1.0)
                interval = 1.0 / max(0.1, hz)
                self.shadow.update_reported_state(
                    device_id=machine_id,
                    reported_state={
                        "sampling_interval_sec": interval,
                        "operating_mode": "AUTO",
                        "firmware_version": "v1.0.0",
                        "config_version": "1.0.0",
                    },
                    actor=AuditSource.SYSTEM,
                )
                self.shadow.update_desired_state(
                    device_id=machine_id,
                    desired_state={
                        "sampling_interval_sec": interval,
                        "operating_mode": "AUTO",
                    },
                    actor=AuditSource.SYSTEM,
                )
        return records

    # -------------------------------------------------------------------------
    # Local Job Execution Engine
    # -------------------------------------------------------------------------
    def execute_job_locally(
        self,
        job_id: str,
        simulate_failure: bool = False,
        failure_error: str = "Simulated execution error",
    ) -> ManagementJobRecord:
        """
        Execute a queued job through its local lifecycle.
        Updates job status, increments attempt logs, synchronizes shadow/fleet state on success,
        and triggers retry handling if simulate_failure is True.
        """
        job = self.jobs.get_job(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        # 1. Start Job
        job = self.jobs.start_job(job_id)

        # 2. Simulate failure if requested
        if simulate_failure:
            return self.jobs.fail_job(job_id, error_message=failure_error, allow_retry=True)

        # 3. Perform work based on job_type
        result: Dict[str, Any] = {"status": "SUCCESS"}

        if job.job_type == JobType.CONFIG_UPDATE:
            desired_patch = job.payload.get("desired", {})
            if desired_patch:
                self.shadow.update_desired_state(job.machine_id, desired_patch, actor=AuditSource.LOCAL_SERVICE)
                # Apply desired into reported (simulating device accepting config)
                self.shadow.sync_reported_from_desired(job.machine_id, actor=AuditSource.LOCAL_SERVICE)
            # Update config version in fleet metadata
            self.fleet.update_device_metadata(
                machine_id=job.machine_id,
                config_version=job.payload.get("config_version", "1.1.0"),
                actor=AuditSource.LOCAL_SERVICE,
            )
            result["applied_config"] = desired_patch

        elif job.job_type == JobType.SYNC_STATE:
            # Sync shadow reported from desired
            self.shadow.sync_reported_from_desired(job.machine_id, actor=AuditSource.LOCAL_SERVICE)
            result["synced"] = True

        elif job.job_type == JobType.OTA_SIMULATION:
            target_fw = job.payload.get("firmware_version", "v1.1.0")
            # Update fleet firmware version
            self.fleet.update_device_metadata(
                machine_id=job.machine_id,
                firmware_version=target_fw,
                actor=AuditSource.LOCAL_SERVICE,
            )
            # Update reported shadow firmware
            self.shadow.update_reported_state(
                device_id=job.machine_id,
                reported_state={"firmware_version": target_fw},
                actor=AuditSource.LOCAL_SERVICE,
            )
            result["new_firmware_version"] = target_fw

        elif job.job_type == JobType.RESTART_SIMULATION:
            # Simulate restart: briefly mark DEGRADED/OFFLINE then ONLINE
            self.fleet.update_connectivity(job.machine_id, ConnectivityState.ONLINE)
            result["restarted"] = True

        elif job.job_type == JobType.COMMAND:
            result["executed_command"] = job.payload

        # 4. Complete Job
        return self.jobs.complete_job(job_id, result=result)

    # -------------------------------------------------------------------------
    # Audit Queries
    # -------------------------------------------------------------------------
    def get_audit_trail(
        self,
        machine_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        limit: int = 100,
    ) -> List[ManagementAuditRecord]:
        return self._audit_backend.list_events(machine_id=machine_id, action=action, limit=limit)
