"""
Unit tests for JobManager.
Covers: job creation, lifecycle state transitions, retry policies, max attempt enforcement, cancellation, and attempt logging.
"""

import pytest
from device_management.jobs import JobManager, InvalidJobStateTransitionError
from device_management.backends.local import LocalJobBackend, LocalAuditBackend
from device_management.repository import DeviceManagementRepository
from device_management.models import JobType, JobStatus
from storage.database import get_engine, get_session_factory, init_db


@pytest.fixture
def job_manager():
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    repo = DeviceManagementRepository(session_factory)
    return JobManager(LocalJobBackend(repo), LocalAuditBackend(repo))


def test_job_creation_and_successful_lifecycle(job_manager):
    job = job_manager.create_job(
        machine_id="CNC-001",
        job_type=JobType.CONFIG_UPDATE,
        payload={"desired": {"operating_mode": "AUTO"}},
        max_attempts=3,
    )
    assert job.status == JobStatus.PENDING
    assert job.attempt == 0

    # Start job
    started = job_manager.start_job(job.job_id)
    assert started.status == JobStatus.IN_PROGRESS
    assert started.attempt == 1

    # Complete job
    completed = job_manager.complete_job(job.job_id, result={"status": "APPLIED"})
    assert completed.status == JobStatus.SUCCEEDED
    assert completed.result == {"status": "APPLIED"}
    assert completed.completed_at is not None

    # Check attempt records
    attempts = job_manager.get_job_attempts(job.job_id)
    assert len(attempts) == 2  # IN_PROGRESS and SUCCEEDED


def test_job_retry_lifecycle_and_max_attempts(job_manager):
    job = job_manager.create_job(
        machine_id="ROBOT-001",
        job_type=JobType.OTA_SIMULATION,
        max_attempts=2,
    )

    # Attempt 1: Start -> Fail -> Should revert to PENDING for retry
    job_manager.start_job(job.job_id)
    fail_1 = job_manager.fail_job(job.job_id, error_message="Network glitch", allow_retry=True)
    assert fail_1.status == JobStatus.PENDING
    assert fail_1.attempt == 1

    # Attempt 2: Start -> Fail -> Reaches max_attempts, should become FAILED
    job_manager.start_job(job.job_id)
    fail_2 = job_manager.fail_job(job.job_id, error_message="Hardware unresponsive", allow_retry=True)
    assert fail_2.status == JobStatus.FAILED
    assert fail_2.attempt == 2
    assert fail_2.completed_at is not None


def test_job_cancellation(job_manager):
    job = job_manager.create_job(
        machine_id="PUMP-001",
        job_type=JobType.RESTART_SIMULATION,
    )
    cancelled = job_manager.cancel_job(job.job_id, reason="Operator aborted restart")
    assert cancelled.status == JobStatus.CANCELLED
    assert cancelled.error == "Operator aborted restart"

    # Cannot cancel already cancelled job
    with pytest.raises(InvalidJobStateTransitionError):
        job_manager.cancel_job(job.job_id)
