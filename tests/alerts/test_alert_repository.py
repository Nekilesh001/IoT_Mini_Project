"""
Unit tests for AlertRepository database persistence, bounded queries, and summary stats.
"""

import pytest
from datetime import datetime, timezone
from storage.database import get_engine, get_session_factory, init_db
from alerts.repository import AlertRepository
from alerts.models import AlertRecord, AlertStatus, AlertSeverity


@pytest.fixture
def repo():
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    return AlertRepository(session_factory)


def test_repository_save_and_query_filters(repo):
    now = datetime.now(timezone.utc)
    rec1 = AlertRecord(
        alert_id="ALT-001",
        rule_id="RULE-1",
        machine_id="CNC-001",
        machine_type="CNC_MACHINING_CENTER",
        alert_code="CODE-1",
        severity=AlertSeverity.WARNING.value,
        title="Warning Alert",
        description="Desc",
        status=AlertStatus.OPEN.value,
        triggered_at=now,
        triggering_measurements={"temp": 82.0},
        current_measurements={"temp": 82.0},
        occurrence_count=1,
    )
    rec2 = AlertRecord(
        alert_id="ALT-002",
        rule_id="RULE-2",
        machine_id="PMP-001",
        machine_type="PUMP",
        alert_code="CODE-2",
        severity=AlertSeverity.CRITICAL.value,
        title="Critical Alert",
        description="Desc",
        status=AlertStatus.ACKNOWLEDGED.value,
        triggered_at=now,
        triggering_measurements={"vib": 9.5},
        current_measurements={"vib": 9.5},
        occurrence_count=2,
    )
    repo.save_alert(rec1)
    repo.save_alert(rec2)

    # Query all
    all_alerts = repo.list_alerts(limit=50)
    assert len(all_alerts) == 2

    # Query by machine_id
    cnc_alerts = repo.list_alerts(machine_id="CNC-001")
    assert len(cnc_alerts) == 1
    assert cnc_alerts[0].machine_id == "CNC-001"

    # Query by severity
    crit_alerts = repo.list_alerts(severity="CRITICAL")
    assert len(crit_alerts) == 1
    assert crit_alerts[0].alert_id == "ALT-002"

    # Summary
    summary = repo.get_summary()
    assert summary["active_total"] == 2
    assert summary["open_total"] == 1
    assert summary["acknowledged_total"] == 1
    assert summary["critical_count"] == 1
    assert summary["warning_count"] == 1
    assert summary["machines_with_active_alerts"] == 2
