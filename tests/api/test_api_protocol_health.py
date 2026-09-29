"""
Unit tests for protocol health endpoint.
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.dependencies import get_telemetry_repository, get_db_engine
from storage.database import get_engine, get_session_factory, init_db
from storage.repository import TelemetryRepository


@pytest.fixture
def client():
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    repo = TelemetryRepository(session_factory)

    app.dependency_overrides[get_db_engine] = lambda: engine
    app.dependency_overrides[get_telemetry_repository] = lambda: repo

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_protocol_health_endpoint(client):
    resp = client.get("/api/protocols/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_protocols"] == 3
    protocols = [p["protocol"] for p in data["protocols"]]
    assert "MODBUS_TCP" in protocols
    assert "OPC_UA" in protocols
    assert "MQTT" in protocols
