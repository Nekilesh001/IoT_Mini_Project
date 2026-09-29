"""
Unit tests for Alert Lifecycle transitions: OPEN -> ACKNOWLEDGED -> RESOLVED.
Also tests invalid transitions (e.g. RESOLVED -> OPEN, or acknowledging an already RESOLVED alert).
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


def test_alert_lifecycle_open_to_acknowledged_to_resolved(repo):
    now = datetime.now(timezone.utc)
    rec = AlertRecord(
        alert_id="ALT-001",
        rule_id="RULE-1",
        machine_id="CNC-001",
        machine_type="CNC_MACHINING_CENTER",
        alert_code="CODE-1",
        severity=AlertSeverity.WARNING.value,
        title="Test Alert",
        description="Test desc",
        status=AlertStatus.OPEN.value,
        triggered_at=now,
        triggering_measurements={"temp": 90.0},
        current_measurements={"temp": 90.0},
        occurrence_count=1,
    )
    repo.save_alert(rec)

    # 1. Verify OPEN
    saved = repo.get_alert_by_id("ALT-001")
    assert saved is not None
    assert saved.status == AlertStatus.OPEN.value
    assert saved.acknowledged_at is None
    assert saved.resolved_at is None

    # 2. Transition OPEN -> ACKNOWLEDGED
    acked = repo.acknowledge_alert("ALT-001")
    assert acked is not None
    assert acked.status == AlertStatus.ACKNOWLEDGED.value
    assert acked.acknowledged_at is not None
    assert acked.resolved_at is None

    # 3. Transition ACKNOWLEDGED -> RESOLVED
    resolved = repo.resolve_alert("ALT-001")
    assert resolved is not None
    assert resolved.status == AlertStatus.RESOLVED.value
    assert resolved.resolved_at is not None


def test_alert_direct_open_to_resolved(repo):
    now = datetime.now(timezone.utc)
    rec = AlertRecord(
        alert_id="ALT-002",
        rule_id="RULE-2",
        machine_id="CNC-001",
        machine_type="CNC_MACHINING_CENTER",
        alert_code="CODE-2",
        severity=AlertSeverity.INFO.value,
        title="Info Alert",
        description="Auto-cleared",
        status=AlertStatus.OPEN.value,
        triggered_at=now,
        triggering_measurements={},
        current_measurements={},
        occurrence_count=1,
    )
    repo.save_alert(rec)

    # Direct OPEN -> RESOLVED
    resolved = repo.resolve_alert("ALT-002")
    assert resolved is not None
    assert resolved.status == AlertStatus.RESOLVED.value
    assert resolved.resolved_at is not None


def test_invalid_lifecycle_transitions(repo):
    now = datetime.now(timezone.utc)
    rec = AlertRecord(
        alert_id="ALT-003",
        rule_id="RULE-3",
        machine_id="CNC-001",
        machine_type="CNC_MACHINING_CENTER",
        alert_code="CODE-3",
        severity=AlertSeverity.CRITICAL.value,
        title="Critical Alert",
        description="Resolved test",
        status=AlertStatus.OPEN.value,
        triggered_at=now,
        triggering_measurements={},
        current_measurements={},
        occurrence_count=1,
    )
    repo.save_alert(rec)
    repo.resolve_alert("ALT-003")

    # Trying to acknowledge an already RESOLVED alert should raise ValueError
    with pytest.raises(ValueError, match="Cannot acknowledge a resolved alert"):
        repo.acknowledge_alert("ALT-003")

    # Trying to resolve an already RESOLVED alert should raise ValueError
    with pytest.raises(ValueError, match="Alert is already resolved"):
        repo.resolve_alert("ALT-003")
