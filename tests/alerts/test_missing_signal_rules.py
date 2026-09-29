"""
Unit tests for MISSING_SIGNAL alert rules.
"""

import pytest
from datetime import datetime, timezone
from alerts.rules import AlertRule, RuleType, AlertSeverity, RuleEvaluator
from edge.models import CanonicalTelemetry, CanonicalSource, CanonicalState, EventType, QualityCode


def test_missing_signal_triggers_when_signal_absent():
    rule = AlertRule(
        rule_id="CNC_MISSING_LOAD",
        machine_type="CNC_MACHINING_CENTER",
        rule_type=RuleType.MISSING_SIGNAL,
        signal="spindle_load_pct",
        severity=AlertSeverity.WARNING,
        alert_code="MISSING_SIGNAL",
        title="Spindle Load Signal Missing",
        description="Spindle load percentage signal missing from telemetry payload",
    )
    evaluator = RuleEvaluator([rule])
    now_str = datetime.now(timezone.utc).isoformat()

    # Telemetry with load present -> No alert
    telem_present = CanonicalTelemetry(
        schema_version="1.0.0",
        event_id="evt_test_1",
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
        measurements={"spindle_speed_rpm": 9000.0, "spindle_load_pct": 55.0},
    )
    assert len(evaluator.evaluate(telem_present)) == 0

    # Telemetry with load absent / None -> Triggers alert
    telem_missing = CanonicalTelemetry(
        schema_version="1.0.0",
        event_id="evt_test_2",
        event_type=EventType.TELEMETRY,
        plant_id="PLANT_01",
        line_id="LINE_A",
        machine_id="CNC-001",
        machine_type="CNC_MACHINING_CENTER",
        source=CanonicalSource(protocol="OPC_UA", endpoint="127.0.0.1:4840", source_address="ns=2;s=CNC-001"),
        event_time=now_str,
        ingestion_time=now_str,
        sequence=2,
        state=CanonicalState(operating="RUNNING", health="HEALTHY"),
        quality=QualityCode.GOOD,
        measurements={"spindle_speed_rpm": 9000.0},
    )
    res = evaluator.evaluate(telem_missing)
    assert len(res) == 1
    assert res[0].rule.rule_id == "CNC_MISSING_LOAD"
