"""
Unit tests for Alert KPI Summary API endpoint (GET /api/alerts/summary).
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

    now = datetime.now(timezone.utc)
    # Seed 1 open critical alert and 1 acknowledged warning alert
    repo.save_alert(AlertRecord(
        alert_id="ALT-SUM-1",
        rule_id="R1",
        machine_id="CNC-001",
        machine_type="CNC_MACHINING_CENTER",
        alert_code="C1",
        severity=AlertSeverity.CRITICAL.value,
        title="CNC Spindle Overheat",
        description="Temp high",
        status=AlertStatus.OPEN.value,
        triggered_at=now,
        triggering_measurements={},
        current_measurements={},
        occurrence_count=1,
    ))
    repo.save_alert(AlertRecord(
        alert_id="ALT-SUM-2",
        rule_id="R2",
        machine_id="CON-001",
        machine_type="CONVEYOR",
        alert_code="C2",
        severity=AlertSeverity.WARNING.value,
        title="Conveyor Current High",
        description="Current high",
        status=AlertStatus.ACKNOWLEDGED.value,
        triggered_at=now,
        triggering_measurements={},
        current_measurements={},
        occurrence_count=1,
    ))

    with TestClient(app) as test_client:
        yield test_client, repo

    app.dependency_overrides.clear()


def test_get_alert_summary(client_and_repo):
    client, _ = client_and_repo

    resp = client.get("/api/alerts/summary")
    assert resp.status_code == 200
    data = resp.json()

    assert data["active_total"] == 2
    assert data["open_total"] == 1
    assert data["acknowledged_total"] == 1
    assert data["critical_count"] == 1
    assert data["warning_count"] == 1
    assert data["machines_with_active_alerts"] == 2
    assert data["recent_alert_count"] == 2
