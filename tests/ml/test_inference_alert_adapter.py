"""
Integration tests for MLAlertAdapter and Operational Alert Engine integration.
"""

from datetime import datetime, timezone
import pytest

from alerts.repository import AlertRepository
from storage.database import get_engine, get_session_factory, init_db
from ml.inference.alert_adapter import MLAlertAdapter
from ml.inference.config import InferenceConfig
from ml.inference.models import AnomalyLabel, InferenceStatus
from ml.inference.result import MLInferenceResult


@pytest.fixture
def session_factory(tmp_path):
    db_file = tmp_path / "test_ml_alerts.db"
    db_url = f"sqlite:///{db_file}"
    engine = get_engine(db_url)
    init_db(engine)
    return get_session_factory(engine)


def test_ml_alert_adapter_anomaly_trigger(session_factory):
    repo = AlertRepository(session_factory)
    adapter = MLAlertAdapter(repo)

    result = MLInferenceResult(
        machine_id="CNC-001",
        machine_type="CNC_MACHINE",
        event_time=datetime.now(timezone.utc),
        anomaly_score=0.88,
        raw_anomaly_score=-0.25,
        anomaly_label=AnomalyLabel.ANOMALOUS,
        predicted_rul_seconds=3600.0,
        status=InferenceStatus.READY,
    )

    alerts = adapter.process_inference_result(result)
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.rule_id == "ML_ANOMALY_DETECTION"
    assert alert.severity == "WARNING"
    assert alert.status == "OPEN"
    assert alert.triggering_measurements["source"] == "ML"


def test_ml_alert_adapter_critical_rul_trigger(session_factory):
    repo = AlertRepository(session_factory)
    adapter = MLAlertAdapter(repo)

    result = MLInferenceResult(
        machine_id="ROB-001",
        machine_type="ROBOT_ARM",
        event_time=datetime.now(timezone.utc),
        anomaly_score=0.2,
        anomaly_label=AnomalyLabel.NORMAL,
        predicted_rul_seconds=450.0,  # Below 600s critical threshold
        predicted_rul_minutes=7.5,
        status=InferenceStatus.READY,
    )

    alerts = adapter.process_inference_result(result)
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.rule_id == "ML_PREDICTIVE_RUL_CRITICAL"
    assert alert.severity == "CRITICAL"
    assert alert.status == "OPEN"
