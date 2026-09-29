"""
Unit tests for Alert API REST endpoints:
GET /api/alerts
GET /api/alerts/active
GET /api/alerts/{id}
GET /api/machines/{machine_id}/alerts
POST /api/alerts/{id}/acknowledge
POST /api/alerts/{id}/resolve
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_alert_repository, get_db_engine
from storage.database import get_engine, get_session_factory, init_db
from alerts.repository import AlertRepository
from alerts.models import AlertRecord, AlertStatus, AlertSeverity


@pytest.fixture
def client_and_repo():
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    repo = AlertRepository(session_factory)

    app.dependency_overrides[get_db_engine] = lambda: engine
    app.dependency_overrides[get_alert_repository] = lambda: repo

    # Seed sample alert
    now = datetime.now(timezone.utc)
    rec = AlertRecord(
        alert_id="ALT-API-001",
        rule_id="PUMP_VIB_CRIT",
        machine_id="PMP-001",
        machine_type="PUMP",
        alert_code="VIB_HIGH",
        severity=AlertSeverity.CRITICAL.value,
        title="Pump High Vibration",
        description="Vibration along X axis exceeded limit",
        status=AlertStatus.OPEN.value,
        triggered_at=now,
        triggering_measurements={"vibration_x_mm_s": 9.42},
        current_measurements={"vibration_x_mm_s": 9.50},
        occurrence_count=1,
    )
    repo.save_alert(rec)

    with TestClient(app) as test_client:
        yield test_client, repo

    app.dependency_overrides.clear()


def test_list_alerts_and_active_alerts(client_and_repo):
    client, _ = client_and_repo

    resp = client.get("/api/alerts")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["alert_id"] == "ALT-API-001"

    resp_active = client.get("/api/alerts/active")
    assert resp_active.status_code == 200
    data_active = resp_active.json()
    assert len(data_active) == 1


def test_get_alert_by_id(client_and_repo):
    client, _ = client_and_repo

    resp = client.get("/api/alerts/ALT-API-001")
    assert resp.status_code == 200
    assert resp.json()["machine_id"] == "PMP-001"

    resp_404 = client.get("/api/alerts/NON-EXISTENT")
    assert resp_404.status_code == 404


def test_acknowledge_and_resolve_lifecycle(client_and_repo):
    client, _ = client_and_repo

    # Acknowledge
    ack_resp = client.post("/api/alerts/ALT-API-001/acknowledge")
    assert ack_resp.status_code == 200
    assert ack_resp.json()["status"] == "ACKNOWLEDGED"

    # Resolve
    res_resp = client.post("/api/alerts/ALT-API-001/resolve")
    assert res_resp.status_code == 200
    assert res_resp.json()["status"] == "RESOLVED"

    # Verify no longer in active
    active_resp = client.get("/api/alerts/active")
    assert len(active_resp.json()) == 0


def test_machine_specific_alerts_endpoint(client_and_repo):
    client, _ = client_and_repo

    resp = client.get("/api/machines/PMP-001/alerts")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp_empty = client.get("/api/machines/CNC-001/alerts")
    assert resp_empty.status_code == 200
    assert len(resp_empty.json()) == 0
