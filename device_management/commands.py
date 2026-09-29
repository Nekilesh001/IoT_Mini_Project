"""
Local Command Abstraction and Handler.
Validates operator commands, maps them to management jobs or shadow updates, and audits every execution.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
import uuid

from device_management.backends.base import AuditBackend
from device_management.jobs import JobManager
from device_management.shadow import DeviceShadowManager
from device_management.models import (
    CommandType,
    JobType,
    AuditAction,
    AuditSource,
    ManagementAuditRecord,
    ManagementJobRecord,
)


class CommandValidationError(Exception):
    """Raised when command parameters fail validation."""
    pass


class CommandHandler:
    """
    Validates and executes administrative commands against machines, creating jobs and audit logs.
    """

    def __init__(
        self,
        shadow_manager: DeviceShadowManager,
        job_manager: JobManager,
        audit_backend: Optional[AuditBackend] = None,
    ):
        self._shadow_manager = shadow_manager
        self._job_manager = job_manager
        self._audit_backend = audit_backend

    def validate_command(self, command_type: CommandType, payload: Dict[str, Any]) -> None:
        """
        Validate command arguments according to industrial constraints.
        """
        if command_type == CommandType.SET_MODE:
            mode = payload.get("mode")
            allowed = {"AUTO", "MANUAL", "MAINTENANCE", "STANDBY", "OFF"}
            if not mode or mode.upper() not in allowed:
                raise CommandValidationError(f"Invalid mode '{mode}'. Allowed modes: {allowed}")

        elif command_type == CommandType.SET_SAMPLING_INTERVAL:
            interval = payload.get("sampling_interval_sec")
            if interval is None or not isinstance(interval, (int, float)) or interval <= 0 or interval > 3600:
                raise CommandValidationError(
                    f"Invalid sampling interval '{interval}'. Must be a positive number <= 3600 seconds."
                )

        elif command_type == CommandType.SIMULATE_RESTART:
            grace_period = payload.get("grace_period_sec", 0)
            if not isinstance(grace_period, (int, float)) or grace_period < 0:
                raise CommandValidationError(f"Invalid grace_period_sec: {grace_period}")

    def execute_command(
        self,
        machine_id: str,
        command_type: CommandType,
        payload: Optional[Dict[str, Any]] = None,
        actor: AuditSource = AuditSource.LOCAL_UI,
        as_job: bool = True,
    ) -> Tuple[Optional[ManagementJobRecord], Dict[str, Any]]:
        """
        Validate and execute an administrative command.
        If as_job is True, dispatches a ManagementJobRecord for asynchronous execution.
        """
        params = payload or {}
        self.validate_command(command_type, params)

        job_record = None
        result = {"status": "ACCEPTED", "command": command_type.value, "machine_id": machine_id}

        if command_type == CommandType.SET_MODE:
            # Update desired shadow and queue config job
            self._shadow_manager.update_desired_state(
                device_id=machine_id,
                desired_state={"operating_mode": params["mode"].upper()},
                actor=actor,
            )
            if as_job:
                job_record = self._job_manager.create_job(
                    machine_id=machine_id,
                    job_type=JobType.CONFIG_UPDATE,
                    payload={"desired": {"operating_mode": params["mode"].upper()}},
                    actor=actor,
                )

        elif command_type == CommandType.SET_SAMPLING_INTERVAL:
            interval = params["sampling_interval_sec"]
            self._shadow_manager.update_desired_state(
                device_id=machine_id,
                desired_state={"sampling_interval_sec": interval},
                actor=actor,
            )
            if as_job:
                job_record = self._job_manager.create_job(
                    machine_id=machine_id,
                    job_type=JobType.CONFIG_UPDATE,
                    payload={"desired": {"sampling_interval_sec": interval}},
                    actor=actor,
                )

        elif command_type == CommandType.REQUEST_STATE_SYNC:
            if as_job:
                job_record = self._job_manager.create_job(
                    machine_id=machine_id,
                    job_type=JobType.SYNC_STATE,
                    payload={},
                    actor=actor,
                )

        elif command_type == CommandType.SIMULATE_RESTART:
            if as_job:
                job_record = self._job_manager.create_job(
                    machine_id=machine_id,
                    job_type=JobType.RESTART_SIMULATION,
                    payload=params,
                    actor=actor,
                )

        else:  # CUSTOM
            if as_job:
                job_record = self._job_manager.create_job(
                    machine_id=machine_id,
                    job_type=JobType.COMMAND,
                    payload=params,
                    actor=actor,
                )

        if job_record:
            result["job_id"] = job_record.job_id

        if self._audit_backend:
            self._audit_backend.record_event(
                ManagementAuditRecord(
                    event_id=f"audit_{uuid.uuid4()}",
                    machine_id=machine_id,
                    action=AuditAction.COMMAND_EXECUTED,
                    actor=actor,
                    timestamp=datetime.now(timezone.utc),
                    after_state={"command": command_type.value, "params": params},
                    result=result,
                )
            )

        return job_record, result
