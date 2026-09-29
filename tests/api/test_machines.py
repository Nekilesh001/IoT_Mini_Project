"""
Unit tests for machines list, detail, and ground-truth isolation.
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from api.main import app
from api.dependencies import get_telemetry_repository, get_db_engine
from storage.database import get_engine, get_session_factory, init_db
from storage.repository import TelemetryRepository
from edge.models import CanonicalTelemetry, CanonicalSource, CanonicalState, EventType, QualityCode


@pytest.fixture
def client_and_repo():
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    repo = TelemetryRepository(session_factory)

    app.dependency_overrides[get_db_engine] = lambda: engine
    app.dependency_overrides[get_telemetry_repository] = lambda: repo

    with TestClient(app) as test_client:
        yield test_client, repo

    app.dependency_overrides.clear()


def test_list_machines(client_and_repo):
    client, _ = client_and_repo
    resp = client.get("/api/machines")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 12
    machine_ids = [m["machine_id"] for m in data]
    assert "CNC-001" in machine_ids
    assert "AGV-001" in machine_ids
    assert "CHL-001" in machine_ids


def test_get_machine_detail_and_ground_truth_isolation(client_and_repo):
    client, repo = client_and_repo

    now_str = datetime.now(timezone.utc).isoformat()
    c = CanonicalTelemetry(
        schema_version="1.0.0",
        event_id="evt_test_det_1",
        event_type=EventType.TELEMETRY,
        plant_id="PLANT_01",
        line_id="LINE_A",
        machine_id="CNC-001",
        machine_type="CNC_MACHINING_CENTER",
        source=CanonicalSource("OPC_UA", "127.0.0.1:4840", "ns=2;s=CNC-001"),
        event_time=now_str,
        ingestion_time=now_str,
        sequence=1,
        state=CanonicalState(operating="RUNNING", health="HEALTHY"),
        quality=QualityCode.GOOD,
        measurements={"spindle_speed_rpm": 9200.0, "vibration_rms_mm_s": 0.85},
        derived={"power_kw": 11.2}
    )
    repo.insert(c)

    resp = client.get("/api/machines/CNC-001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["machine_id"] == "CNC-001"
    assert data["operating_state"] == "RUNNING"
    assert data["current_measurements"]["spindle_speed_rpm"] == 9200.0
    assert len(data["signals"]) > 0

    # STRICT GROUND-TRUTH ISOLATION CHECK
    raw_text = resp.text
    assert "degradation_level" not in raw_text
    assert "hidden_wear_counter" not in raw_text
    assert "fault_label" not in raw_text
    assert "scenario_id" not in raw_text
    assert "_simulationGroundTruth" not in raw_text


def test_get_unknown_machine_returns_404(client_and_repo):
    client, _ = client_and_repo
    resp = client.get("/api/machines/UNKNOWN-999")
    assert resp.status_code == 404
