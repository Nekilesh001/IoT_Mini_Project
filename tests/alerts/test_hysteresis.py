"""
Unit tests for Hysteresis and Auto-clearing logic.
Verifies that alerts trigger above threshold and only auto-clear below hysteresis clear_threshold.
"""

import pytest
from datetime import datetime, timezone
from storage.database import get_engine, get_session_factory, init_db
from alerts.repository import AlertRepository
from alerts.rules import AlertRule, RuleType, AlertSeverity
from alerts.engine import AlertEngine
from alerts.models import AlertStatus
from edge.models import CanonicalTelemetry, CanonicalSource, CanonicalState, EventType, QualityCode


def make_telem(vibration: float):
    now_str = datetime.now(timezone.utc).isoformat()
    return CanonicalTelemetry(
        schema_version="1.0.0",
        event_id="evt_test_hyst",
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


def test_hysteresis_trigger_and_clear_behavior():
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    repo = AlertRepository(session_factory)

    # Trigger > 8.0, Clear < 6.5
    rule = AlertRule(
        rule_id="PUMP_VIB_CRIT",
        machine_type="PUMP",
        rule_type=RuleType.THRESHOLD,
        signal="vibration_x_mm_s",
        operator=">",
        threshold=8.0,
        clear_threshold=6.5,
        severity=AlertSeverity.CRITICAL,
        alert_code="VIB_HIGH",
        title="Pump High Vibration",
        description="Vibration exceeded critical limit",
    )
    alert_engine = AlertEngine(rules=[rule], repository=repo)

    # 1. Telemetry = 8.5 (> 8.0) -> Triggers alert
    alert_engine.process_telemetry(make_telem(8.5))
    active = repo.list_active_alerts()
    assert len(active) == 1
    assert active[0].status == AlertStatus.OPEN.value

    # 2. Telemetry drops to 7.2 (< 8.0, but > 6.5 hysteresis zone) -> Alert remains ACTIVE (OPEN)
    alert_engine.process_telemetry(make_telem(7.2))
    active = repo.list_active_alerts()
    assert len(active) == 1
    assert active[0].status == AlertStatus.OPEN.value

    # 3. Telemetry drops to 6.0 (< 6.5 clear threshold) -> Alert is automatically RESOLVED
    alert_engine.process_telemetry(make_telem(6.0))
    active = repo.list_active_alerts()
    assert len(active) == 0

    history = repo.list_alerts(status="RESOLVED")
    assert len(history) == 1
    assert history[0].status == AlertStatus.RESOLVED.value
