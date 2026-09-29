"""
Tests for AlertEngine cooldown restore (Fix C6) and
AlertRepository.get_all_active_alerts().
"""

from datetime import datetime, timezone
import pytest

from alerts.repository import AlertRepository
from alerts.engine import AlertEngine
from alerts.rules import AlertSeverity, AlertStatus, get_default_rules
from storage.database import get_engine, get_session_factory, init_db


@pytest.fixture
def session_factory(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'test_alerts_c6.db'}"
    engine = get_engine(db_url)
    init_db(engine)
    return get_session_factory(engine)


class TestAlertRepositoryGetAllActive:
    """Test get_all_active_alerts returns only open/ack alerts."""

    def test_returns_open_alerts(self, session_factory):
        repo = AlertRepository(session_factory)
        repo.create_alert(
            rule_id="TEST_RULE",
            machine_id="CNC-001",
            machine_type="CNC_MACHINING_CENTER",
            alert_code="T-001",
            severity=AlertSeverity.WARNING,
            title="Test",
            description="desc",
            triggering_measurements={"val": 1},
        )
        alerts = repo.get_all_active_alerts()
        assert len(alerts) == 1
        assert alerts[0].status == AlertStatus.OPEN.value

    def test_does_not_return_resolved_alerts(self, session_factory):
        repo = AlertRepository(session_factory)
        alert = repo.create_alert(
            rule_id="RESOLVE_ME",
            machine_id="PMP-001",
            machine_type="INDUSTRIAL_PUMP",
            alert_code="T-002",
            severity=AlertSeverity.CRITICAL,
            title="Will Resolve",
            description="desc",
            triggering_measurements={"val": 2},
        )
        repo.resolve_alert(alert.alert_id)
        active = repo.get_all_active_alerts()
        ids = [a.alert_id for a in active]
        assert alert.alert_id not in ids

    def test_returns_multiple_machines(self, session_factory):
        repo = AlertRepository(session_factory)
        for mid in ["M-001", "M-002", "M-003"]:
            repo.create_alert(
                rule_id="MULTI",
                machine_id=mid,
                machine_type="TEST",
                alert_code="T-003",
                severity=AlertSeverity.WARNING,
                title="Multi",
                description="desc",
                triggering_measurements={},
            )
        alerts = repo.get_all_active_alerts()
        assert len(alerts) == 3


class TestAlertEngineCooldownRestore:
    """Fix C6: AlertEngine must restore cooldown from DB on init."""

    def test_engine_restores_cooldown_on_startup(self, session_factory):
        """
        If active alerts already exist in the DB, engine must pre-populate
        _last_trigger_times so it doesn't immediately re-create duplicate alerts.
        """
        repo = AlertRepository(session_factory)
        # Pre-create an OPEN alert directly in DB
        triggered_at = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        repo.create_alert(
            rule_id="PUMP_VIBRATION_CRITICAL",
            machine_id="PMP-001",
            machine_type="INDUSTRIAL_PUMP",
            alert_code="ALT-PMP-01",
            severity=AlertSeverity.CRITICAL,
            title="Pre-existing pump alert",
            description="Simulates alert from before worker restart",
            triggering_measurements={"vibration_x_mm_s": 5.0},
        )

        # Now start the engine — it should restore the cooldown
        engine = AlertEngine(repository=repo, rules=get_default_rules())

        # The cooldown key for PMP-001:PUMP_VIBRATION_CRITICAL should be set
        cooldown_key = "PMP-001:PUMP_VIBRATION_CRITICAL"
        assert cooldown_key in engine._last_trigger_times, (
            "Engine must restore cooldown from DB active alerts on startup"
        )

    def test_engine_without_active_alerts_has_empty_cooldowns(self, session_factory):
        """Fresh DB with no alerts → no cooldowns to restore."""
        repo = AlertRepository(session_factory)
        engine = AlertEngine(repository=repo, rules=get_default_rules())
        # Should be empty (nothing to restore)
        assert len(engine._last_trigger_times) == 0

    def test_engine_does_not_restore_resolved_alerts(self, session_factory):
        """Resolved alerts must NOT populate cooldown state."""
        repo = AlertRepository(session_factory)
        alert = repo.create_alert(
            rule_id="CNC_SPINDLE_TEMP_CRITICAL",
            machine_id="CNC-001",
            machine_type="CNC_MACHINING_CENTER",
            alert_code="ALT-CNC-02",
            severity=AlertSeverity.CRITICAL,
            title="Resolved alert",
            description="This was resolved before restart",
            triggering_measurements={"spindle_temperature_c": 85.0},
        )
        repo.resolve_alert(alert.alert_id)

        engine = AlertEngine(repository=repo, rules=get_default_rules())
        cooldown_key = "CNC-001:CNC_SPINDLE_TEMP_CRITICAL"
        assert cooldown_key not in engine._last_trigger_times, (
            "Resolved alerts must NOT be in cooldown state"
        )
