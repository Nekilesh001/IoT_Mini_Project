"""
Integration tests for Wokwi database persistence and FastAPI REST / SSE endpoints.
"""

from datetime import datetime, timezone
import json
import pytest
from fastapi.testclient import TestClient

from storage.database import get_engine, get_session_factory, init_db
from storage.repository import TelemetryRepository
from edge.service import EdgeIngestionService
from protocols.wokwi.normalizer import WokwiPayloadNormalizer
from protocols.wokwi.registry import get_external_device_registry
from api.main import app


@pytest.fixture
def sqlite_repo(tmp_path):
    db_path = tmp_path / "test_wokwi.db"
    db_url = f"sqlite:///{db_path}"
    engine = get_engine(db_url)
    init_db(engine)
    session_factory = get_session_factory(engine)
    return TelemetryRepository(session_factory)


@pytest.fixture
def client():
    return TestClient(app)


def test_wokwi_storage_persistence(sqlite_repo):
    registry = get_external_device_registry()
    edge_service = EdgeIngestionService(profiles=registry.get_all_machine_profiles())
    normalizer = WokwiPayloadNormalizer()

    payload = json.dumps({
        "deviceId": "IOT-SENSOR-001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sequence": 100,
        "readings": {"temperatureC": 31.8, "humidityPct": 65.4}
    })

    reading, _ = normalizer.normalize(payload)
    ingestion_res = edge_service.ingest_reading(reading)
    assert ingestion_res.canonical_telemetry is not None

    # Persist to database
    inserted = sqlite_repo.insert(ingestion_res.canonical_telemetry)
    assert inserted is True

    # Retrieve latest record
    latest = sqlite_repo.get_latest_by_machine("IOT-SENSOR-001")
    assert latest is not None
    assert latest.machine_id == "IOT-SENSOR-001"
    assert latest.machine_type == "ENVIRONMENT_SENSOR"
    assert latest.measurements["temperature_c"] == 31.8
    assert latest.measurements["humidity_pct"] == 65.4
    assert latest.sequence == 100


def test_api_list_iot_devices(client):
    response = client.get("/api/iot-devices")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    sensor = next((d for d in data if d["device_id"] == "IOT-SENSOR-001"), None)
    assert sensor is not None
    assert sensor["device_type"] == "ENVIRONMENT_SENSOR"
    assert sensor["device_class"] == "EXTERNAL_IOT"
    assert sensor["ingress_broker"] == "broker.hivemq.com"


def test_api_get_iot_device_detail(client):
    response = client.get("/api/iot-devices/IOT-SENSOR-001")
    assert response.status_code == 200
    sensor = response.json()
    assert sensor["device_id"] == "IOT-SENSOR-001"
    assert sensor["hardware"] == "Raspberry Pi Pico W + DHT22 + LED"


def test_api_bridge_status(client):
    response = client.get("/api/iot-devices/bridge/status")
    assert response.status_code == 200
    status = response.json()
    assert "enabled" in status
    assert status["broker"] == "broker.hivemq.com"
