"""
Unit tests for RATE_OF_CHANGE alert rules.
"""

import pytest
from datetime import datetime, timezone, timedelta
from alerts.rules import AlertRule, RuleType, AlertSeverity, RuleEvaluator
from edge.models import CanonicalTelemetry, CanonicalSource, CanonicalState, EventType, QualityCode


def make_telem(machine_id: str, machine_type: str, measurements: dict, dt: datetime):
    return CanonicalTelemetry(
        schema_version="1.0.0",
        event_id="evt_test",
        event_type=EventType.TELEMETRY,
        plant_id="PLANT_01",
        line_id="LINE_A",
        machine_id=machine_id,
        machine_type=machine_type,
        source=CanonicalSource(protocol="MQTT", endpoint="127.0.0.1:1883", source_address="topic/cnc"),
        event_time=dt.isoformat(),
        ingestion_time=dt.isoformat(),
        sequence=1,
        state=CanonicalState(operating="RUNNING", health="HEALTHY"),
        quality=QualityCode.GOOD,
        measurements=measurements,
    )


def test_rate_of_change_rule_triggers_on_rapid_rise():
    rule = AlertRule(
        rule_id="CNC_TEMP_SPIKE",
        machine_type="CNC_MACHINING_CENTER",
        rule_type=RuleType.RATE_OF_CHANGE,
        signal="spindle_temperature_c",
        threshold=5.0,  # > 5 °C per second
        severity=AlertSeverity.WARNING,
        alert_code="TEMP_SPIKE",
        title="Spindle Rapid Heating",
        description="Spindle temperature rising unusually fast",
    )
    evaluator = RuleEvaluator([rule])
    t0 = datetime(2026, 9, 29, 10, 0, 0, tzinfo=timezone.utc)

    # First tick: 40.0 °C
    t1 = make_telem("CNC-001", "CNC_MACHINING_CENTER", {"spindle_temperature_c": 40.0}, t0)
    res1 = evaluator.evaluate(t1)
    assert len(res1) == 0

    # Second tick: 42.0 °C after 1s (Rate = 2.0 °C/s <= 5.0) -> No alert
    t2 = make_telem("CNC-001", "CNC_MACHINING_CENTER", {"spindle_temperature_c": 42.0}, t0 + timedelta(seconds=1))
    res2 = evaluator.evaluate(t2)
    assert len(res2) == 0

    # Third tick: 50.0 °C after 1s (Rate = 8.0 °C/s > 5.0) -> Triggers alert
    t3 = make_telem("CNC-001", "CNC_MACHINING_CENTER", {"spindle_temperature_c": 50.0}, t0 + timedelta(seconds=2))
    res3 = evaluator.evaluate(t3)
    assert len(res3) == 1
    assert res3[0].rule.rule_id == "CNC_TEMP_SPIKE"
    assert res3[0].observed_value == 8.0
