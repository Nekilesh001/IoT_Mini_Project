"""
Unit tests for CommandHandler.
Covers: command validation, shadow updating, job dispatching, and audit logging.
"""

import pytest
from device_management.commands import CommandHandler, CommandValidationError
from device_management.shadow import DeviceShadowManager
from device_management.jobs import JobManager
from device_management.backends.local import (
    LocalDeviceStateBackend,
    LocalJobBackend,
    LocalAuditBackend,
)
from device_management.repository import DeviceManagementRepository
from device_management.models import CommandType, JobType
from storage.database import get_engine, get_session_factory, init_db


@pytest.fixture
def command_handler():
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    repo = DeviceManagementRepository(session_factory)
    shadow_mgr = DeviceShadowManager(LocalDeviceStateBackend(repo), LocalAuditBackend(repo))
    job_mgr = JobManager(LocalJobBackend(repo), LocalAuditBackend(repo))
    return CommandHandler(shadow_mgr, job_mgr, LocalAuditBackend(repo)), repo


def test_command_validation(command_handler):
    handler, _ = command_handler

    # Invalid mode
    with pytest.raises(CommandValidationError):
        handler.validate_command(CommandType.SET_MODE, {"mode": "INVALID_MODE"})

    # Invalid sampling interval
    with pytest.raises(CommandValidationError):
        handler.validate_command(CommandType.SET_SAMPLING_INTERVAL, {"sampling_interval_sec": -5})


def test_execute_set_mode_command(command_handler):
    handler, repo = command_handler

    job, result = handler.execute_command(
        machine_id="CNC-001",
        command_type=CommandType.SET_MODE,
        payload={"mode": "AUTO"},
        as_job=True,
    )
    assert result["status"] == "ACCEPTED"
    assert job is not None
    assert job.job_type == JobType.CONFIG_UPDATE

    # Verify shadow desired state was updated
    shadow = repo.get_shadow("CNC-001")
    assert shadow.desired_state["operating_mode"] == "AUTO"

    # Verify audit trail
    audits = repo.list_audit_events(machine_id="CNC-001")
    assert len(audits) >= 1
