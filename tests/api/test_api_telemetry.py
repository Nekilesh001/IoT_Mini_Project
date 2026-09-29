"""
Unit tests for telemetry endpoints and historical queries.
"""

import pytest
from datetime import datetime, timezone, timedelta
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


def test_get_latest_telemetry_and_history(client_and_repo):
    client, repo = client_and_repo
    base_time = datetime.now(timezone.utc)

    # Insert 3 records for CNC-001
    for seq in range(1, 4):
        t_str = (base_time + timedelta(seconds=seq)).isoformat()
        c = CanonicalTelemetry(
            schema_version="1.0.0",
            event_id=f"evt_hist_{seq}",
            event_type=EventType.TELEMETRY,
            plant_id="PLANT_01",
            line_id="LINE_A",
            machine_id="CNC-001",
            machine_type="CNC_MACHINING_CENTER",
            source=CanonicalSource("OPC_UA", "127.0.0.1:4840", "ns=2;s=CNC-001"),
            event_time=t_str,
            ingestion_time=t_str,
            sequence=seq,
            state=CanonicalState("RUNNING", "HEALTHY"),
            quality=QualityCode.GOOD,
            measurements={"spindle_speed_rpm": 9000.0 + seq, "vibration_rms_mm_s": 0.5 + seq * 0.1}
        )
        repo.insert(c)

    # 1. Latest telemetry
    resp = client.get("/api/telemetry/latest")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["sequence"] == 3

    # 2. History endpoint
    resp_hist = client.get("/api/machines/CNC-001/history?limit=10")
    assert resp_hist.status_code == 200
    data_hist = resp_hist.json()
    assert data_hist["total_records"] == 3
    assert len(data_hist["records"]) == 3

    # 3. Signal filtered history
    resp_sig = client.get("/api/machines/CNC-001/history?signals=spindle_speed_rpm")
    assert resp_sig.status_code == 200
    data_sig = resp_sig.json()
    assert "spindle_speed_rpm" in data_sig["records"][0]["measurements"]
    assert "vibration_rms_mm_s" not in data_sig["records"][0]["measurements"]


def test_invalid_time_range_returns_400(client_and_repo):
    client, _ = client_and_repo
    start = "2026-09-29T12:00:00Z"
    end = "2026-09-29T10:00:00Z"  # End before start
    resp = client.get(f"/api/machines/CNC-001/history?start={start}&end={end}")
    assert resp.status_code == 400
