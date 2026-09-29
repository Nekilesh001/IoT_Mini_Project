"""
Unit tests for factory summary endpoint.
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


def test_factory_summary_empty_and_with_telemetry(client_and_repo):
    client, repo = client_and_repo

    # 1. Summary before telemetry
    resp = client.get("/api/factory/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_machines"] == 12
    assert data["total_telemetry_records"] == 0

    # 2. Add telemetry for CNC-001
    now_str = datetime.now(timezone.utc).isoformat()
    c = CanonicalTelemetry(
        schema_version="1.0.0",
        event_id="evt_test_sum_1",
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
        measurements={"spindle_speed_rpm": 9200.0}
    )
    repo.insert(c)

    # 3. Summary after telemetry
    resp = client.get("/api/factory/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_telemetry_records"] == 1
    assert data["states"]["running"] >= 1
    assert len(data["protocols"]) == 3
