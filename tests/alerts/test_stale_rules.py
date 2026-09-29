"""
Unit tests for STALE_SIGNAL and bad quality rules.
"""

import pytest
from datetime import datetime, timezone
from alerts.rules import AlertRule, RuleType, AlertSeverity, RuleEvaluator
from edge.models import CanonicalTelemetry, CanonicalSource, CanonicalState, EventType, QualityCode


def test_stale_signal_rule_triggers_on_stale_quality():
    rule = AlertRule(
        rule_id="VISION_STALE_FRAME",
        machine_type="VISION_SYSTEM",
        rule_type=RuleType.STALE_SIGNAL,
        signal="defect_rate_pct",
        severity=AlertSeverity.WARNING,
        alert_code="STALE_SIGNAL",
        title="Vision Signal Stale",
        description="Defect rate telemetry is marked stale or missing by edge validator",
    )
    evaluator = RuleEvaluator([rule])
    now_str = datetime.now(timezone.utc).isoformat()

    # Good quality
    telem_good = CanonicalTelemetry(
        schema_version="1.0.0",
        event_id="evt_vis_1",
        event_type=EventType.TELEMETRY,
        plant_id="PLANT_01",
        line_id="LINE_A",
        machine_id="VIS-001",
        machine_type="VISION_SYSTEM",
        source=CanonicalSource(protocol="REST", endpoint="127.0.0.1:8080", source_address="/vision/001"),
        event_time=now_str,
        ingestion_time=now_str,
        sequence=1,
        state=CanonicalState(operating="RUNNING", health="HEALTHY"),
        quality=QualityCode.GOOD,
        measurements={"defect_rate_pct": 1.2},
    )
    assert len(evaluator.evaluate(telem_good)) == 0

    # Stale quality
    telem_stale = CanonicalTelemetry(
        schema_version="1.0.0",
        event_id="evt_vis_2",
        event_type=EventType.TELEMETRY,
        plant_id="PLANT_01",
        line_id="LINE_A",
        machine_id="VIS-001",
        machine_type="VISION_SYSTEM",
        source=CanonicalSource(protocol="REST", endpoint="127.0.0.1:8080", source_address="/vision/001"),
        event_time=now_str,
        ingestion_time=now_str,
        sequence=2,
        state=CanonicalState(operating="RUNNING", health="HEALTHY"),
        quality=QualityCode.STALE,
        measurements={"defect_rate_pct": 1.2},
    )
    res = evaluator.evaluate(telem_stale)
    assert len(res) == 1
    assert res[0].rule.rule_id == "VISION_STALE_FRAME"
