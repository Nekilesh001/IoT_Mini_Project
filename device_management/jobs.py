"""
Job Manager & Execution Engine.
Orchestrates management job lifecycles (PENDING -> IN_PROGRESS -> SUCCEEDED/FAILED/CANCELLED),
configurable retries, attempt logs, and local execution of configuration, OTA simulations, and state synchronization.
"""

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
import uuid

from device_management.backends.base import JobBackend, AuditBackend
from device_management.models import (
    JobType,
    JobStatus,
    ManagementJobRecord,
    JobAttemptRecord,
    AuditAction,
    AuditSource,
    ManagementAuditRecord,
)


class InvalidJobStateTransitionError(Exception):
    """Raised when an invalid job lifecycle transition is attempted."""
    pass


class JobManager:
    """
    Business logic layer for management job scheduling, retry policies, and lifecycle transitions.
    """

    def __init__(
        self,
        job_backend: JobBackend,
        audit_backend: Optional[AuditBackend] = None,
    ):
        self._job_backend = job_backend
        self._audit_backend = audit_backend

    def create_job(
        self,
        machine_id: str,
        job_type: JobType,
        payload: Optional[Dict[str, Any]] = None,
        max_attempts: int = 3,
        actor: AuditSource = AuditSource.LOCAL_UI,
    ) -> ManagementJobRecord:
        """
        Create and queue a new management job.
        """
        job = ManagementJobRecord(
            job_id=f"job_{uuid.uuid4().hex[:12]}",
            machine_id=machine_id,
            job_type=job_type,
            payload=payload or {},
            status=JobStatus.PENDING,
            attempt=0,
            max_attempts=max(1, max_attempts),
            created_at=datetime.now(timezone.utc),
        )

        saved = self._job_backend.create_job(job)

        if self._audit_backend:
            self._audit_backend.record_event(
                ManagementAuditRecord(
                    event_id=f"audit_{uuid.uuid4()}",
                    machine_id=machine_id,
                    action=AuditAction.JOB_CREATED,
                    actor=actor,
                    timestamp=datetime.now(timezone.utc),
                    after_state=saved.model_dump(mode="json"),
                    result={"job_id": saved.job_id, "type": saved.job_type.value},
                )
            )

        return saved

    def start_job(
        self,
        job_id: str,
        actor: AuditSource = AuditSource.SYSTEM,
    ) -> ManagementJobRecord:
        """
        Transition job to IN_PROGRESS and increment attempt counter.
        """
        job = self._job_backend.get_job(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        if job.status not in (JobStatus.PENDING, JobStatus.FAILED):
            raise InvalidJobStateTransitionError(
                f"Cannot start job '{job_id}' from status '{job.status.value}'"
            )

        job.status = JobStatus.IN_PROGRESS
        job.attempt += 1
        job.started_at = datetime.now(timezone.utc)
        job.error = None

        saved = self._job_backend.update_job(job)

        # Record attempt start
        attempt = JobAttemptRecord(
            attempt_id=f"att_{uuid.uuid4().hex[:8]}",
            job_id=job_id,
            attempt_number=job.attempt,
            status=JobStatus.IN_PROGRESS,
            started_at=datetime.now(timezone.utc),
        )
        self._job_backend.record_attempt(attempt)

        if self._audit_backend:
            self._audit_backend.record_event(
                ManagementAuditRecord(
                    event_id=f"audit_{uuid.uuid4()}",
                    machine_id=job.machine_id,
                    action=AuditAction.JOB_STARTED,
                    actor=actor,
                    timestamp=datetime.now(timezone.utc),
                    after_state={"job_id": job.job_id, "status": job.status.value, "attempt": job.attempt},
                    result={"status": "IN_PROGRESS"},
                )
            )

        return saved

    def complete_job(
        self,
        job_id: str,
        result: Optional[Dict[str, Any]] = None,
        actor: AuditSource = AuditSource.SYSTEM,
    ) -> ManagementJobRecord:
        """
        Transition job to SUCCEEDED.
        """
        job = self._job_backend.get_job(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        if job.status != JobStatus.IN_PROGRESS:
            raise InvalidJobStateTransitionError(
                f"Cannot complete job '{job_id}' from status '{job.status.value}'"
            )

        now = datetime.now(timezone.utc)
        job.status = JobStatus.SUCCEEDED
        job.result = result or {"success": True}
        job.completed_at = now

        saved = self._job_backend.update_job(job)

        # Record attempt completion
        attempt = JobAttemptRecord(
            attempt_id=f"att_{uuid.uuid4().hex[:8]}",
            job_id=job_id,
            attempt_number=job.attempt,
            status=JobStatus.SUCCEEDED,
            result=job.result,
            started_at=job.started_at or now,
            completed_at=now,
        )
        self._job_backend.record_attempt(attempt)

        if self._audit_backend:
            self._audit_backend.record_event(
                ManagementAuditRecord(
                    event_id=f"audit_{uuid.uuid4()}",
                    machine_id=job.machine_id,
                    action=AuditAction.JOB_COMPLETED,
                    actor=actor,
                    timestamp=now,
                    after_state={"job_id": job.job_id, "status": job.status.value, "result": job.result},
                    result={"status": "SUCCEEDED"},
                )
            )

        return saved

    def fail_job(
        self,
        job_id: str,
        error_message: str,
        allow_retry: bool = True,
        actor: AuditSource = AuditSource.SYSTEM,
    ) -> ManagementJobRecord:
        """
        Transition job on failure.
        If attempt < max_attempts and allow_retry is True, sets status to PENDING for retry;
        otherwise marks job as permanently FAILED.
        """
        job = self._job_backend.get_job(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        now = datetime.now(timezone.utc)
        job.error = error_message

        # Record attempt failure
        attempt = JobAttemptRecord(
            attempt_id=f"att_{uuid.uuid4().hex[:8]}",
            job_id=job_id,
            attempt_number=job.attempt,
            status=JobStatus.FAILED,
            error=error_message,
            started_at=job.started_at or now,
            completed_at=now,
        )
        self._job_backend.record_attempt(attempt)

        can_retry = allow_retry and (job.attempt < job.max_attempts)

        if can_retry:
            job.status = JobStatus.PENDING
            saved = self._job_backend.update_job(job)
            action = AuditAction.JOB_RETRIED
        else:
            job.status = JobStatus.FAILED
            job.completed_at = now
            saved = self._job_backend.update_job(job)
            action = AuditAction.JOB_FAILED

        if self._audit_backend:
            self._audit_backend.record_event(
                ManagementAuditRecord(
                    event_id=f"audit_{uuid.uuid4()}",
                    machine_id=job.machine_id,
                    action=action,
                    actor=actor,
                    timestamp=now,
                    after_state={"job_id": job.job_id, "status": job.status.value, "attempt": job.attempt, "error": error_message},
                    error=error_message,
                    result={"status": job.status.value, "can_retry": can_retry},
                )
            )

        return saved

    def cancel_job(
        self,
        job_id: str,
        reason: Optional[str] = None,
        actor: AuditSource = AuditSource.LOCAL_UI,
    ) -> ManagementJobRecord:
        """
        Cancel a pending or running job.
        """
        job = self._job_backend.get_job(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        if job.status in (JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED):
            raise InvalidJobStateTransitionError(
                f"Cannot cancel job '{job_id}' in terminal state '{job.status.value}'"
            )

        now = datetime.now(timezone.utc)
        job.status = JobStatus.CANCELLED
        job.error = reason or "Job cancelled by operator"
        job.completed_at = now

        saved = self._job_backend.update_job(job)

        if self._audit_backend:
            self._audit_backend.record_event(
                ManagementAuditRecord(
                    event_id=f"audit_{uuid.uuid4()}",
                    machine_id=job.machine_id,
                    action=AuditAction.JOB_CANCELLED,
                    actor=actor,
                    timestamp=now,
                    after_state={"job_id": job.job_id, "status": job.status.value, "reason": job.error},
                    result={"status": "CANCELLED"},
                )
            )

        return saved

    def get_job(self, job_id: str) -> Optional[ManagementJobRecord]:
        return self._job_backend.get_job(job_id)

    def list_jobs(
        self,
        machine_id: Optional[str] = None,
        status: Optional[JobStatus] = None,
        limit: int = 100,
    ) -> List[ManagementJobRecord]:
        return self._job_backend.list_jobs(machine_id=machine_id, status=status, limit=limit)

    def get_job_attempts(self, job_id: str) -> List[JobAttemptRecord]:
        return self._job_backend.get_attempts(job_id)
