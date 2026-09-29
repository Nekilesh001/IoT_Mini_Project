"""
Unit tests for Alert data models and schemas.
Ensures ground-truth variables are strictly excluded from Alert models.
"""

import pytest
from datetime import datetime, timezone
from alerts.models import AlertRecord, AlertStatus, AlertSeverity
from api.schemas.alerts import AlertResponse, AlertSummaryResponse


def test_alert_record_model_instantiation():
    now = datetime.now(timezone.utc)
    rec = AlertRecord(
        alert_id="ALT-12345",
        rule_id="PUMP_VIBRATION_CRITICAL",
        machine_id="PMP-001",
        machine_type="PUMP",
        alert_code="VIB_HIGH",
        severity=AlertSeverity.CRITICAL.value,
        title="Excessive Vibration",
        description="Vibration along X axis exceeded 8.0 mm/s",
        status=AlertStatus.OPEN.value,
        triggered_at=now,
        triggering_measurements={"vibration_x_mm_s": 9.45},
        current_measurements={"vibration_x_mm_s": 9.60},
        occurrence_count=1,
    )

    assert rec.alert_id == "ALT-12345"
    assert rec.severity == "CRITICAL"
    assert rec.status == "OPEN"
    assert rec.occurrence_count == 1
    assert "vibration_x_mm_s" in rec.triggering_measurements


def test_alert_models_exclude_hidden_ground_truth():
    """Verify that alert models do not contain hidden simulation parameters like wear or fault labels."""
    fields = AlertRecord.__table__.columns.keys()
    for forbidden in ["wear_level", "degradation_level", "ground_truth", "hidden_state", "fault_flag"]:
        assert forbidden not in fields, f"Forbidden simulation variable {forbidden} exposed in AlertRecord"

    response_fields = AlertResponse.model_fields.keys()
    for forbidden in ["wear_level", "degradation_level", "ground_truth", "hidden_state"]:
        assert forbidden not in response_fields, f"Forbidden simulation variable {forbidden} in AlertResponse"
