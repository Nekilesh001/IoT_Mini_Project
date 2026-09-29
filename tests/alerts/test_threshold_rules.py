"""
Unit tests for THRESHOLD rules with various operators and severities.
"""

import pytest
from datetime import datetime, timezone
from alerts.rules import AlertRule, RuleType, AlertSeverity, RuleEvaluator
from edge.models import CanonicalTelemetry, CanonicalSource, CanonicalState, EventType, QualityCode


def make_telem(machine_id: str, machine_type: str, measurements: dict):
    now_str = datetime.now(timezone.utc).isoformat()
    return CanonicalTelemetry(
        schema_version="1.0.0",
        event_id="evt_test",
        event_type=EventType.TELEMETRY,
        plant_id="PLANT_01",
        line_id="LINE_A",
        machine_id=machine_id,
        machine_type=machine_type,
        source=CanonicalSource(protocol="OPC_UA", endpoint="127.0.0.1:4840", source_address="ns=2;s=CNC-001"),
        event_time=now_str,
        ingestion_time=now_str,
        sequence=1,
        state=CanonicalState(operating="RUNNING", health="HEALTHY"),
        quality=QualityCode.GOOD,
        measurements=measurements,
    )


def test_threshold_less_than():
    rule = AlertRule(
        rule_id="AGV_BATTERY_LOW",
        machine_type="AGV",
        rule_type=RuleType.THRESHOLD,
        signal="battery_soc",
        operator="<",
        threshold=20.0,
        severity=AlertSeverity.WARNING,
        alert_code="AGV_LOW_BATT",
        title="Low Battery",
        description="AGV battery state of charge is low",
    )
    evaluator = RuleEvaluator([rule])

    # Normal battery (85%)
    assert len(evaluator.evaluate(make_telem("AGV-001", "AGV", {"battery_soc": 85.0}))) == 0

    # Low battery (18.5%)
    res = evaluator.evaluate(make_telem("AGV-001", "AGV", {"battery_soc": 18.5}))
    assert len(res) == 1
    assert res[0].triggered is True
    assert res[0].rule.severity == AlertSeverity.WARNING


def test_threshold_critical_and_warning_hierarchy():
    rules = [
        AlertRule(
            rule_id="PUMP_VIB_WARN",
            machine_type="PUMP",
            rule_type=RuleType.THRESHOLD,
            signal="vibration_x_mm_s",
            operator=">",
            threshold=5.0,
            severity=AlertSeverity.WARNING,
            alert_code="VIB_WARN",
            title="Vibration Warning",
            description="Vibration high",
        ),
        AlertRule(
            rule_id="PUMP_VIB_CRIT",
            machine_type="PUMP",
            rule_type=RuleType.THRESHOLD,
            signal="vibration_x_mm_s",
            operator=">",
            threshold=8.0,
            severity=AlertSeverity.CRITICAL,
            alert_code="VIB_CRIT",
            title="Vibration Critical",
            description="Vibration critical",
        ),
    ]
    evaluator = RuleEvaluator(rules)

    # Moderate vibration triggers warning only
    res1 = evaluator.evaluate(make_telem("PMP-001", "PUMP", {"vibration_x_mm_s": 6.2}))
    assert len(res1) == 1
    assert res1[0].rule.severity == AlertSeverity.WARNING

    # Extreme vibration triggers both
    res2 = evaluator.evaluate(make_telem("PMP-001", "PUMP", {"vibration_x_mm_s": 9.5}))
    assert len(res2) == 2
