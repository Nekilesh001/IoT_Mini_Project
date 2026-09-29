"""
Integration tests for Realtime SSE Alert and Telemetry streaming.
"""

import asyncio
import pytest
from datetime import datetime, timezone
from storage.database import get_engine, get_session_factory, init_db
from storage.repository import TelemetryRepository
from alerts.repository import AlertRepository
from alerts.models import AlertRecord, AlertSeverity, AlertStatus
from api.dependencies import get_factory_profiles
from api.services.realtime_service import RealtimeService


@pytest.mark.asyncio
async def test_realtime_service_alert_streaming():
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    repo = TelemetryRepository(session_factory)
    alert_repo = AlertRepository(session_factory)
    profiles = get_factory_profiles()

    now = datetime.now(timezone.utc)
    rec = AlertRecord(
        alert_id="ALT-RT-001",
        rule_id="PUMP_VIB_CRIT",
        machine_id="PMP-001",
        machine_type="PUMP",
        alert_code="VIB_CRIT",
        severity=AlertSeverity.CRITICAL.value,
        title="Pump High Vibration",
        description="Excessive vibration",
        status=AlertStatus.OPEN.value,
        triggered_at=now,
        triggering_measurements={"vibration_x_mm_s": 9.5},
        current_measurements={"vibration_x_mm_s": 9.5},
        occurrence_count=1,
    )
    alert_repo.save_alert(rec)

    service = RealtimeService(
        repository=repo,
        profiles=profiles,
        alert_repository=alert_repo,
        interval_seconds=0.1
    )

    # Test dedicated alert_event_generator
    alert_gen = service.alert_event_generator()
    first_alert_event = await anext(alert_gen)

    assert first_alert_event.startswith("data: ")
    assert "ALERT_UPDATE" in first_alert_event
    assert "ALT-RT-001" in first_alert_event
    assert "PMP-001" in first_alert_event
