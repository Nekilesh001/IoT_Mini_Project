"""
Unit tests for health endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_db_engine
from storage.database import get_engine, init_db


@pytest.fixture
def client():
    # Use in-memory SQLite for fast testing
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    app.dependency_overrides[get_db_engine] = lambda: engine
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_check_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database_connected"] is True
    assert "timestamp" in data
