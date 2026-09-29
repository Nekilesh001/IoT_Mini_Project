"""
Integration tests for FastAPI Device Management and Fleet REST endpoints.
Covers:
  - GET /api/devices
  - GET /api/devices/{machine_id}
  - GET /api/devices/{machine_id}/shadow
  - PATCH /api/devices/{machine_id}/shadow
  - POST /api/devices/{machine_id}/shadow/sync
  - GET /api/jobs
  - POST /api/jobs
  - POST /api/jobs/{job_id}/execute
  - POST /api/jobs/{job_id}/cancel
  - GET /api/fleet/summary
  - GET /api/management/audit
"""

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from storage.database import get_engine, get_session_factory, init_db
from device_management.repository import DeviceManagementRepository
from device_management.service import DeviceManagementService
from device_management.backends.local import (
    LocalDeviceStateBackend,
    LocalFleetBackend,
    LocalJobBackend,
    LocalAuditBackend,
)
from api.dependencies import get_device_management_service, get_factory_profiles


@pytest.fixture
def client():
    app = create_app()
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    repo = DeviceManagementRepository(session_factory)
    service = DeviceManagementService(
        state_backend=LocalDeviceStateBackend(repo),
        fleet_backend=LocalFleetBackend(repo),
        job_backend=LocalJobBackend(repo),
        audit_backend=LocalAuditBackend(repo),
    )
    # Bootstrap
    profiles = get_factory_profiles()
    service.bootstrap_fleet(profiles)

    app.dependency_overrides[get_device_management_service] = lambda: service

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_api_list_and_get_devices(client):
    res = client.get("/api/devices")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 12

    # Get single device
    res_single = client.get("/api/devices/CNC-001")
    assert res_single.status_code == 200
    assert res_single.json()["machine_id"] == "CNC-001"


def test_api_shadow_get_patch_and_sync(client):
    # Get shadow
    res = client.get("/api/devices/CNC-001/shadow")
    assert res.status_code == 200
    shadow = res.json()
    assert shadow["device_id"] == "CNC-001"

    # Patch desired state
    res_patch = client.patch(
        "/api/devices/CNC-001/shadow",
        json={"desired": {"operating_mode": "MANUAL", "sampling_interval_sec": 5.0}},
    )
    assert res_patch.status_code == 200
    updated_shadow = res_patch.json()
    assert updated_shadow["is_sync_pending"] is True
    assert updated_shadow["delta"]["operating_mode"] == "MANUAL"

    # Sync shadow
    res_sync = client.post("/api/devices/CNC-001/shadow/sync")
    assert res_sync.status_code == 200
    synced_shadow = res_sync.json()
    assert synced_shadow["is_sync_pending"] is False
    assert synced_shadow["reported_state"]["operating_mode"] == "MANUAL"


def test_api_jobs_lifecycle_and_execution(client):
    # Create job
    res_create = client.post(
        "/api/jobs",
        json={
            "machine_id": "PUMP-001",
            "job_type": "CONFIG_UPDATE",
            "payload": {"desired": {"operating_mode": "AUTO"}},
            "max_attempts": 3,
        },
    )
    assert res_create.status_code == 201
    job = res_create.json()
    job_id = job["job_id"]
    assert job["status"] == "PENDING"

    # Execute job locally
    res_exec = client.post(f"/api/jobs/{job_id}/execute")
    assert res_exec.status_code == 200
    exec_job = res_exec.json()
    assert exec_job["status"] == "SUCCEEDED"

    # Query attempts
    res_attempts = client.get(f"/api/jobs/{job_id}/attempts")
    assert res_attempts.status_code == 200
    assert len(res_attempts.json()) >= 1


def test_api_fleet_summary_and_audit(client):
    # Fleet summary
    res_sum = client.get("/api/fleet/summary")
    assert res_sum.status_code == 200
    summary = res_sum.json()
    assert summary["total_machines"] == 12

    # Audit trail
    res_audit = client.get("/api/management/audit?limit=20")
    assert res_audit.status_code == 200
    assert isinstance(res_audit.json(), list)
