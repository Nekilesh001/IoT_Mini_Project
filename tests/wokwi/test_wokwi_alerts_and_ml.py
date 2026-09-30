"""
Tests for Wokwi alert rules and complete ML isolation.
"""

from datetime import datetime, timezone
import json
import pytest

from alerts.engine import AlertEngine
from alerts.models import AlertSeverity
from alerts.rules import create_default_rules
from edge.service import EdgeIngestionService
from ml.inference.models import InferenceStatus
from ml.inference.service import MLInferenceService
from protocols.wokwi.normalizer import WokwiPayloadNormalizer
from protocols.wokwi.registry import get_external_device_registry


from storage.database import get_engine, get_session_factory, init_db
from alerts.repository import AlertRepository


@pytest.fixture
def edge_service():
    registry = get_external_device_registry()
    return EdgeIngestionService(profiles=registry.get_all_machine_profiles())


@pytest.fixture
def alert_engine(tmp_path):
    db_path = tmp_path / "test_alerts.db"
    engine = get_engine(f"sqlite:///{db_path}")
    init_db(engine)
    session_factory = get_session_factory(engine)
    repo = AlertRepository(session_factory)
    return AlertEngine(repository=repo, rules=create_default_rules())


@pytest.fixture
def ml_service():
    return MLInferenceService()


def test_wokwi_alert_temperature_warning(edge_service, alert_engine):
    normalizer = WokwiPayloadNormalizer()
    payload = json.dumps({
        "deviceId": "IOT-SENSOR-001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sequence": 1,
        "readings": {"temperatureC": 31.5, "humidityPct": 60.0}
    })

    reading, _ = normalizer.normalize(payload)
    res = edge_service.ingest_reading(reading)
    assert res.canonical_telemetry is not None

    triggered = alert_engine.process_telemetry(res.canonical_telemetry)
    assert len(triggered) >= 1

    warn_alert = next((a for a in triggered if a.rule_id == "ENV_TEMP_HIGH_WARNING"), None)
    assert warn_alert is not None
    assert warn_alert.severity == AlertSeverity.WARNING
    assert warn_alert.machine_id == "IOT-SENSOR-001"


def test_wokwi_alert_temperature_critical(edge_service, alert_engine):
    normalizer = WokwiPayloadNormalizer()
    payload = json.dumps({
        "deviceId": "IOT-SENSOR-001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sequence": 2,
        "readings": {"temperatureC": 36.5, "humidityPct": 60.0}
    })

    reading, _ = normalizer.normalize(payload)
    res = edge_service.ingest_reading(reading)

    triggered = alert_engine.process_telemetry(res.canonical_telemetry)
    crit_alert = next((a for a in triggered if a.rule_id == "ENV_TEMP_HIGH_CRITICAL"), None)
    assert crit_alert is not None
    assert crit_alert.severity == AlertSeverity.CRITICAL


def test_wokwi_ml_isolation_guarantee(edge_service, ml_service):
    """
    Guarantees that external IoT telemetry is explicitly excluded from industrial
    ML feature pipelines and does not corrupt anomaly/RUL state.
    """
    normalizer = WokwiPayloadNormalizer()
    payload = json.dumps({
        "deviceId": "IOT-SENSOR-001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sequence": 1,
        "readings": {"temperatureC": 28.0, "humidityPct": 50.0}
    })

    reading, _ = normalizer.normalize(payload)
    res = edge_service.ingest_reading(reading)
    canonical = res.canonical_telemetry

    # Execute ML inference check
    ml_result = ml_service.infer(canonical)
    
    # Must NOT be READY (status must be NOT_READY) and error_message must note exclusion
    assert ml_result.status == InferenceStatus.NOT_READY
    assert "excluded from industrial predictive maintenance" in ml_result.error_message
    
    # Temporal buffer for industrial machines must NOT contain IOT-SENSOR-001
    if ml_service.feature_pipeline:
        active_machine_ids = ml_service.feature_pipeline.buffer.get_all_machine_ids()
        assert "IOT-SENSOR-001" not in active_machine_ids
