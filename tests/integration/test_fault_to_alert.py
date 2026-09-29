"""
End-to-End Integration Test for Phase 6:
FaultScenario -> Simulator Condition -> Machine Telemetry -> Edge Ingestion -> Canonical Telemetry -> RuleEngine -> Alert Persistence -> API.
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from simulator.runtime.factory_runtime import FactorySimulator
from scenarios.manager import FaultScenarioManager, create_standard_scenarios
from edge.service import EdgeIngestionService
from protocols.models import ProtocolReading, ProtocolType
from alerts.rules import create_default_rules
from alerts.engine import AlertEngine
from alerts.repository import AlertRepository
from storage.database import get_engine, get_session_factory, init_db
from api.main import app
from api.dependencies import get_alert_repository, get_db_engine


def test_end_to_end_conveyor_jam_to_alert():
    # 1. Setup in-memory DB and repositories
    db_engine = get_engine("sqlite:///:memory:")
    init_db(db_engine)
    session_factory = get_session_factory(db_engine)
    alert_repo = AlertRepository(session_factory)

    app.dependency_overrides[get_db_engine] = lambda: db_engine
    app.dependency_overrides[get_alert_repository] = lambda: alert_repo

    # 2. Setup Factory, Edge, Scenario Manager, and Alert Engine
    factory = FactorySimulator(seed=42)
    factory.start()
    profiles = {m.machine_id: m.profile for m in factory.get_all_machines()}
    edge_service = EdgeIngestionService(profiles=profiles)

    scenario_mgr = FaultScenarioManager(factory)
    scenario_mgr.register_scenarios(create_standard_scenarios())
    alert_engine = AlertEngine(rules=create_default_rules(), repository=alert_repo)

    # Step A: Baseline normal tick for CON-001
    conv = factory.get_machine("CON-001")
    factory.step(1.0)
    snap_normal = conv.generate_snapshot()
    reading_normal = ProtocolReading(
        machine_id="CON-001",
        machine_type="INDUSTRIAL_CONVEYOR",
        protocol=ProtocolType.MODBUS_TCP,
        timestamp=str(snap_normal.timestamp),
        sequence=1,
        measurements=dict(snap_normal.public_measurements),
        source_address="127.0.0.1:5020/unit=3",
        raw_payload=[]
    )
    res_normal = edge_service.ingest_reading(reading_normal)
    alerts_normal = alert_engine.process_telemetry(res_normal.canonical_telemetry)
    assert len(alerts_normal) == 0

    # Step B: Inject Sudden Fault -> Conveyor Belt Jam
    scenario_mgr.start_scenario("CONVEYOR_BELT_JAM")
    factory.step(1.0)
    snap_fault = conv.generate_snapshot()
    reading_fault = ProtocolReading(
        machine_id="CON-001",
        machine_type="INDUSTRIAL_CONVEYOR",
        protocol=ProtocolType.MODBUS_TCP,
        timestamp=str(snap_fault.timestamp),
        sequence=2,
        measurements=dict(snap_fault.public_measurements),
        source_address="127.0.0.1:5020/unit=3",
        raw_payload=[]
    )
    res_fault = edge_service.ingest_reading(reading_fault)
    alerts_fault = alert_engine.process_telemetry(res_fault.canonical_telemetry)

    assert len(alerts_fault) >= 1
    jam_alert = next((a for a in alerts_fault if "CONVEYOR_BELT_JAM" in a.rule_id or "CONV" in a.rule_id), None)
    assert jam_alert is not None
    assert jam_alert.machine_id == "CON-001"
    assert jam_alert.triggering_measurements["drive_motor_current_a"] > 18.0

    # Step C: Verify Alert via FastAPI REST API Client
    with TestClient(app) as client:
        resp = client.get("/api/alerts/active")
        assert resp.status_code == 200
        active_list = resp.json()
        assert any(a["alert_id"] == jam_alert.alert_id for a in active_list)

        # Acknowledge the alert
        ack_resp = client.post(f"/api/alerts/{jam_alert.alert_id}/acknowledge")
        assert ack_resp.status_code == 200
        assert ack_resp.json()["status"] == "ACKNOWLEDGED"

    # Step D: Clear Fault Scenario and verify Hysteresis Auto-Recovery
    scenario_mgr.stop_scenario("CONVEYOR_BELT_JAM")
    factory.step(1.0)
    snap_cleared = conv.generate_snapshot()
    reading_cleared = ProtocolReading(
        machine_id="CON-001",
        machine_type="INDUSTRIAL_CONVEYOR",
        protocol=ProtocolType.MODBUS_TCP,
        timestamp=str(snap_cleared.timestamp),
        sequence=3,
        measurements=dict(snap_cleared.public_measurements),
        source_address="127.0.0.1:5020/unit=3",
        raw_payload=[]
    )
    res_cleared = edge_service.ingest_reading(reading_cleared)
    alert_engine.process_telemetry(res_cleared.canonical_telemetry)

    # Alert should now be resolved in repository
    resolved_rec = alert_repo.get_alert_by_id(jam_alert.alert_id)
    assert resolved_rec.status == "RESOLVED"
    assert resolved_rec.resolved_at is not None

    app.dependency_overrides.clear()


def test_end_to_end_pump_bearing_degradation_to_alert():
    # 1. Setup DB
    db_engine = get_engine("sqlite:///:memory:")
    init_db(db_engine)
    session_factory = get_session_factory(db_engine)
    alert_repo = AlertRepository(session_factory)

    app.dependency_overrides[get_db_engine] = lambda: db_engine
    app.dependency_overrides[get_alert_repository] = lambda: alert_repo

    factory = FactorySimulator(seed=42)
    factory.start()
    profiles = {m.machine_id: m.profile for m in factory.get_all_machines()}
    edge_service = EdgeIngestionService(profiles=profiles)

    scenario_mgr = FaultScenarioManager(factory)
    scenario_mgr.register_scenarios(create_standard_scenarios())
    alert_engine = AlertEngine(rules=create_default_rules(), repository=alert_repo)

    pump = factory.get_machine("PMP-001")

    # Start progressive bearing degradation
    scenario_mgr.start_scenario("PUMP_BEARING_WEAR")

    # Advance 15 seconds so degradation ramps up vibration
    for _ in range(15):
        scenario_mgr.advance_scenarios(dt_seconds=1.0)
        factory.step(1.0)

    snap = pump.generate_snapshot()
    reading = ProtocolReading(
        machine_id="PMP-001",
        machine_type="INDUSTRIAL_PUMP",
        protocol=ProtocolType.MQTT,
        timestamp=str(snap.timestamp),
        sequence=15,
        measurements=dict(snap.public_measurements),
        source_address="tcp://127.0.0.1:1883/factory/PMP-001/telemetry",
        raw_payload=[]
    )
    res = edge_service.ingest_reading(reading)
    alerts = alert_engine.process_telemetry(res.canonical_telemetry)

    assert len(alerts) >= 1
    vib_alert = next((a for a in alerts if "PUMP_VIB" in a.rule_id), None)
    assert vib_alert is not None
    assert vib_alert.machine_id == "PMP-001"
    assert "vibration_x_mm_s" in vib_alert.triggering_measurements

    app.dependency_overrides.clear()
