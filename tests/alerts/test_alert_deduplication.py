"""
Unit tests for Alert deduplication and occurrence counting.
Verifies that multiple consecutive ticks with the same rule violation do not spawn duplicate alerts.
"""

import pytest
from datetime import datetime, timezone
from storage.database import get_engine, get_session_factory, init_db
from alerts.repository import AlertRepository
from alerts.rules import AlertRule, RuleType, AlertSeverity
from alerts.engine import AlertEngine
from edge.models import CanonicalTelemetry, CanonicalSource, CanonicalState, EventType, QualityCode


def make_telem(vibration: float):
    now_str = datetime.now(timezone.utc).isoformat()
    return CanonicalTelemetry(
        schema_version="1.0.0",
        event_id="evt_test_dedup",
        event_type=EventType.TELEMETRY,
        plant_id="PLANT_01",
        line_id="LINE_A",
        machine_id="PMP-001",
        machine_type="PUMP",
        source=CanonicalSource(protocol="MQTT", endpoint="127.0.0.1:1883", source_address="factory/PMP-001/telemetry"),
        event_time=now_str,
        ingestion_time=now_str,
        sequence=1,
        state=CanonicalState(operating="RUNNING", health="HEALTHY"),
        quality=QualityCode.GOOD,
        measurements={"vibration_x_mm_s": vibration},
    )


def test_alert_deduplication_increments_occurrence_count():
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    repo = AlertRepository(session_factory)

    rule = AlertRule(
        rule_id="PUMP_VIB_CRIT",
        machine_type="PUMP",
        rule_type=RuleType.THRESHOLD,
        signal="vibration_x_mm_s",
        operator=">",
        threshold=8.0,
        severity=AlertSeverity.CRITICAL,
        alert_code="VIB_HIGH",
        title="Pump High Vibration",
        description="Vibration exceeded critical limit",
    )
    alert_engine = AlertEngine(rules=[rule], repository=repo)

    # 1. First tick -> Creates 1 new active alert
    alerts1 = alert_engine.process_telemetry(make_telem(8.5))
    assert len(alerts1) == 1
    assert alerts1[0].occurrence_count == 1
    active = repo.list_active_alerts()
    assert len(active) == 1
    alert_id = alerts1[0].alert_id

    # 2. Second tick -> Same condition, updates occurrence count to 2, does not create new row
    alerts2 = alert_engine.process_telemetry(make_telem(9.0))
    assert len(alerts2) == 1
    assert alerts2[0].alert_id == alert_id
    assert alerts2[0].occurrence_count == 2
    assert alerts2[0].current_measurements["vibration_x_mm_s"] == 9.0

    # 3. Third tick -> Still high, occurrence count to 3
    alerts3 = alert_engine.process_telemetry(make_telem(9.2))
    assert len(alerts3) == 1
    assert alerts3[0].occurrence_count == 3

    # Total active alerts in repository is still 1
    active_final = repo.list_active_alerts()
    assert len(active_final) == 1
    assert active_final[0].occurrence_count == 3
