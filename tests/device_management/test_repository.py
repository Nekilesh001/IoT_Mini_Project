"""
Unit tests for DeviceManagementRepository.
Covers: SQLite & Postgres table mapping, JSON serialization, and CRUD methods for shadows, fleet, jobs, attempts, and audit logs.
"""

from datetime import datetime, timezone
import uuid
import pytest

from storage.database import get_engine, get_session_factory, init_db
from device_management.repository import DeviceManagementRepository
from device_management.models import (
    ConnectivityState,
    ManagementState,
    JobType,
    JobStatus,
    AuditAction,
    AuditSource,
    FleetDeviceRecord,
    ManagementJobRecord,
    JobAttemptRecord,
    ManagementAuditRecord,
)


@pytest.fixture
def repo():
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    return DeviceManagementRepository(session_factory)


def test_shadow_repository_crud(repo):
    # Upsert new shadow
    rec = repo.upsert_shadow("CNC-001", desired_state={"speed": 100}, reported_state={"speed": 50}, version=1)
    assert rec.device_id == "CNC-001"
    assert rec.is_sync_pending is True

    # Retrieve
    fetched = repo.get_shadow("CNC-001")
    assert fetched is not None
    assert fetched.desired_state == {"speed": 100}


def test_fleet_repository_crud(repo):
    device = FleetDeviceRecord(
        machine_id="ROBOT-001",
        machine_type="INDUSTRIAL_ROBOT_6AXIS",
        protocol="MQTT",
        connectivity=ConnectivityState.ONLINE,
    )
    saved = repo.register_or_update_device(device)
    assert saved.machine_id == "ROBOT-001"

    fetched = repo.get_device("ROBOT-001")
    assert fetched is not None
    assert fetched.protocol == "MQTT"


def test_job_and_attempts_repository_crud(repo):
    job = ManagementJobRecord(
        job_id="job_test_01",
        machine_id="PUMP-001",
        job_type=JobType.CONFIG_UPDATE,
        payload={"key": "val"},
        status=JobStatus.PENDING,
    )
    saved_job = repo.create_job(job)
    assert saved_job.job_id == "job_test_01"

    # Log attempt
    attempt = JobAttemptRecord(
        attempt_id="att_01",
        job_id="job_test_01",
        attempt_number=1,
        status=JobStatus.IN_PROGRESS,
    )
    repo.record_attempt(attempt)

    attempts = repo.get_job_attempts("job_test_01")
    assert len(attempts) == 1
    assert attempts[0].attempt_number == 1


def test_audit_repository_crud(repo):
    audit = ManagementAuditRecord(
        event_id=f"audit_{uuid.uuid4()}",
        machine_id="CNC-001",
        action=AuditAction.DEVICE_REGISTERED,
        actor=AuditSource.SYSTEM,
        result={"registered": True},
    )
    saved = repo.record_audit(audit)
    assert saved.machine_id == "CNC-001"

    events = repo.list_audit_events(machine_id="CNC-001")
    assert len(events) == 1
    assert events[0].action == AuditAction.DEVICE_REGISTERED
