"""
Unit tests for Alert Rule evaluation logic and RuleEvaluator.
"""

import pytest
from datetime import datetime, timezone
from alerts.rules import AlertRule, RuleType, AlertSeverity, RuleEvaluator
from edge.models import CanonicalTelemetry, CanonicalSource, CanonicalState, EventType, QualityCode


def make_telemetry(machine_id: str, machine_type: str, measurements: dict, state: str = "RUNNING"):
    now_str = datetime.now(timezone.utc).isoformat()
    return CanonicalTelemetry(
        schema_version="1.0.0",
        event_id="evt_test",
        event_type=EventType.TELEMETRY,
        plant_id="PLANT_01",
        line_id="LINE_A",
        machine_id=machine_id,
        machine_type=machine_type,
        source=CanonicalSource(protocol="MQTT", endpoint="127.0.0.1:1883", source_address=f"factory/{machine_id}/telemetry"),
        event_time=now_str,
        ingestion_time=now_str,
        sequence=1,
        state=CanonicalState(operating=state, health="HEALTHY"),
        quality=QualityCode.GOOD,
        measurements=measurements,
    )


def test_rule_evaluator_evaluates_threshold_greater():
    rule = AlertRule(
        rule_id="CNC_TEMP_HIGH",
        machine_type="CNC_MACHINING_CENTER",
        rule_type=RuleType.THRESHOLD,
        signal="spindle_temperature_c",
        operator=">",
        threshold=80.0,
        severity=AlertSeverity.WARNING,
        alert_code="CNC_TEMP_WARN",
        title="Spindle High Temperature",
        description="Spindle temp exceeded limit",
    )
    evaluator = RuleEvaluator([rule])

    # Normal
    telem_normal = make_telemetry("CNC-001", "CNC_MACHINING_CENTER", {"spindle_temperature_c": 65.0})
    res_normal = evaluator.evaluate(telem_normal)
    assert len(res_normal) == 0

    # Over limit
    telem_over = make_telemetry("CNC-001", "CNC_MACHINING_CENTER", {"spindle_temperature_c": 85.5})
    res_over = evaluator.evaluate(telem_over)
    assert len(res_over) == 1
    assert res_over[0].rule.rule_id == "CNC_TEMP_HIGH"
    assert res_over[0].triggered is True
    assert res_over[0].observed_value == 85.5


def test_rule_evaluator_skips_different_machine_type():
    rule = AlertRule(
        rule_id="CNC_TEMP_HIGH",
        machine_type="CNC_MACHINING_CENTER",
        rule_type=RuleType.THRESHOLD,
        signal="spindle_temperature_c",
        operator=">",
        threshold=80.0,
        severity=AlertSeverity.WARNING,
        alert_code="CNC_TEMP_WARN",
        title="Spindle High Temperature",
        description="Spindle temp exceeded limit",
    )
    evaluator = RuleEvaluator([rule])

    # Telemetry for a PUMP should not trigger CNC rule
    telem_pump = make_telemetry("PMP-001", "PUMP", {"spindle_temperature_c": 95.0})
    res = evaluator.evaluate(telem_pump)
    assert len(res) == 0
