"""
Unit tests for FleetManager.
Covers: machine registration, inventory queries, connectivity transitions, metadata updating, and fleet summary aggregation.
"""

import pytest
from simulator.runtime.factory_runtime import FactorySimulator
from device_management.fleet import FleetManager
from device_management.backends.local import LocalFleetBackend, LocalAuditBackend
from device_management.repository import DeviceManagementRepository
from device_management.models import ConnectivityState, ManagementState
from storage.database import get_engine, get_session_factory, init_db


@pytest.fixture
def fleet_manager():
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    repo = DeviceManagementRepository(session_factory)
    return FleetManager(LocalFleetBackend(repo), LocalAuditBackend(repo))


def test_fleet_bootstrap_and_queries(fleet_manager):
    sim = FactorySimulator(seed=42)
    profiles = {m.machine_id: m.profile for m in sim.get_all_machines()}

    records = fleet_manager.register_all_from_profiles(profiles)
    assert len(records) == 12

    # Query single machine
    m = fleet_manager.get_machine("CNC-001")
    assert m is not None
    assert m.machine_id == "CNC-001"
    assert m.machine_type == "CNC_MACHINING_CENTER"
    assert m.connectivity == ConnectivityState.ONLINE

    # List all machines
    all_devs = fleet_manager.list_machines()
    assert len(all_devs) == 12


def test_fleet_connectivity_and_metadata_updates(fleet_manager):
    sim = FactorySimulator(seed=42)
    profiles = {m.machine_id: m.profile for m in sim.get_all_machines()}
    fleet_manager.register_all_from_profiles(profiles)

    # Change connectivity
    updated = fleet_manager.update_connectivity("PMP-001", ConnectivityState.DEGRADED)
    assert updated is not None
    assert updated.connectivity == ConnectivityState.DEGRADED

    # Filter by connectivity
    degraded = fleet_manager.list_machines(connectivity=ConnectivityState.DEGRADED)
    assert len(degraded) == 1
    assert degraded[0].machine_id == "PMP-001"

    # Update metadata
    meta_updated = fleet_manager.update_device_metadata(
        machine_id="CNC-001",
        software_version="1.2.0",
        firmware_version="v2.0.0",
        config_version="1.1.0",
        management_state=ManagementState.MAINTENANCE,
        metadata_patch={"zone": "ZONE_WEST"},
    )
    assert meta_updated.software_version == "1.2.0"
    assert meta_updated.firmware_version == "v2.0.0"
    assert meta_updated.management_state == ManagementState.MAINTENANCE
    assert meta_updated.metadata.get("zone") == "ZONE_WEST"


def test_fleet_summary_metrics(fleet_manager):
    sim = FactorySimulator(seed=42)
    profiles = {m.machine_id: m.profile for m in sim.get_all_machines()}
    fleet_manager.register_all_from_profiles(profiles)

    # Mark one offline, one degraded
    fleet_manager.update_connectivity("CNC-002", ConnectivityState.OFFLINE)
    fleet_manager.update_connectivity("ROB-001", ConnectivityState.DEGRADED)

    summary = fleet_manager.get_fleet_summary()
    assert summary.total_machines == 12
    assert summary.online_count == 10
    assert summary.offline_count == 1
    assert summary.degraded_count == 1
    assert "OPC_UA" in summary.machines_by_protocol
    assert "MODBUS_TCP" in summary.machines_by_protocol
    assert "MQTT" in summary.machines_by_protocol
