"""
Unit tests for COMPOSITE alert rules requiring multiple simultaneous abnormal conditions.
"""

import pytest
from datetime import datetime, timezone
from alerts.rules import AlertRule, RuleType, AlertSeverity, RuleEvaluator
from edge.models import CanonicalTelemetry, CanonicalSource, CanonicalState, EventType, QualityCode


def make_telem(measurements: dict):
    now_str = datetime.now(timezone.utc).isoformat()
    return CanonicalTelemetry(
        schema_version="1.0.0",
        event_id="evt_test_comp",
        event_type=EventType.TELEMETRY,
        plant_id="PLANT_01",
        line_id="LINE_A",
        machine_id="CNC-001",
        machine_type="CNC_MACHINING_CENTER",
        source=CanonicalSource(protocol="OPC_UA", endpoint="127.0.0.1:4840", source_address="ns=2;s=CNC-001"),
        event_time=now_str,
        ingestion_time=now_str,
        sequence=1,
        state=CanonicalState(operating="RUNNING", health="HEALTHY"),
        quality=QualityCode.GOOD,
        measurements=measurements,
    )


def test_composite_rule_triggers_only_when_all_conditions_met():
    rule = AlertRule(
        rule_id="CNC_THERMAL_OVERLOAD",
        machine_type="CNC_MACHINING_CENTER",
        rule_type=RuleType.COMPOSITE,
        conditions=[
            {"signal": "spindle_temperature_c", "operator": ">", "threshold": 75.0},
            {"signal": "spindle_load_pct", "operator": ">", "threshold": 90.0},
        ],
        severity=AlertSeverity.CRITICAL,
        alert_code="THERMAL_OVERLOAD",
        title="Spindle Thermal Overload",
        description="High spindle temperature combined with excessive spindle load",
    )
    evaluator = RuleEvaluator([rule])

    # Case 1: Normal temp, high load -> No alert
    assert len(evaluator.evaluate(make_telem({"spindle_temperature_c": 50.0, "spindle_load_pct": 95.0}))) == 0

    # Case 2: High temp, normal load -> No alert
    assert len(evaluator.evaluate(make_telem({"spindle_temperature_c": 80.0, "spindle_load_pct": 60.0}))) == 0

    # Case 3: High temp AND high load -> Triggers CRITICAL alert
    res = evaluator.evaluate(make_telem({"spindle_temperature_c": 78.5, "spindle_load_pct": 93.0}))
    assert len(res) == 1
    assert res[0].rule.rule_id == "CNC_THERMAL_OVERLOAD"
    assert res[0].rule.severity == AlertSeverity.CRITICAL
    assert res[0].observed_value == {"spindle_temperature_c": 78.5, "spindle_load_pct": 93.0}
