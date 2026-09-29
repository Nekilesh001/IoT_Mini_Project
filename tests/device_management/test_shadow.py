"""
Unit tests for DeviceShadowState and DeviceShadowManager.
Covers: desired/reported updates, delta calculation, version increments, optimistic version conflicts, and synchronization.
"""

import pytest
from device_management.state import DeviceShadowState, VersionConflictError
from device_management.shadow import DeviceShadowManager
from device_management.backends.local import LocalDeviceStateBackend, LocalAuditBackend
from device_management.repository import DeviceManagementRepository
from storage.database import get_engine, get_session_factory, init_db


@pytest.fixture
def in_memory_repo():
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    return DeviceManagementRepository(session_factory)


@pytest.fixture
def shadow_manager(in_memory_repo):
    state_backend = LocalDeviceStateBackend(in_memory_repo)
    audit_backend = LocalAuditBackend(in_memory_repo)
    return DeviceShadowManager(state_backend, audit_backend)


def test_shadow_state_delta_computation():
    state = DeviceShadowState(
        device_id="CNC-001",
        desired_state={"sampling_interval_sec": 5, "operating_mode": "AUTO"},
        reported_state={"sampling_interval_sec": 10, "operating_mode": "AUTO"},
    )
    assert state.is_sync_pending is True
    assert state.delta == {"sampling_interval_sec": 5}

    # Desired matches reported
    state.update_reported({"sampling_interval_sec": 5})
    assert state.is_sync_pending is False
    assert state.delta == {}


def test_shadow_state_version_increment_and_conflict():
    state = DeviceShadowState(device_id="PUMP-001", version=1)
    assert state.version == 1

    # Valid update with matching version
    state.update_desired({"mode": "MANUAL"}, expected_version=1)
    assert state.version == 2

    # Attempt update with wrong expected version
    with pytest.raises(VersionConflictError):
        state.update_desired({"mode": "AUTO"}, expected_version=1)


def test_shadow_manager_desired_and_sync_flow(shadow_manager):
    # Initial empty shadow
    shadow = shadow_manager.get_shadow("ROBOT-001")
    assert shadow.device_id == "ROBOT-001"
    assert shadow.version == 1

    # Update desired state
    updated = shadow_manager.update_desired_state(
        device_id="ROBOT-001",
        desired_state={"speed_pct": 80, "safety_stop": False},
    )
    assert updated.version == 2
    assert updated.is_sync_pending is True
    assert updated.delta == {"speed_pct": 80, "safety_stop": False}

    # Update reported state partially
    part_reported = shadow_manager.update_reported_state(
        device_id="ROBOT-001",
        reported_state={"speed_pct": 80},
    )
    assert part_reported.is_sync_pending is True
    assert part_reported.delta == {"safety_stop": False}

    # Sync reported from desired
    synced = shadow_manager.sync_reported_from_desired("ROBOT-001")
    assert synced.is_sync_pending is False
    assert synced.delta == {}
    assert synced.reported_state["safety_stop"] is False
