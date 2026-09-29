"""
Unit tests for realtime SSE telemetry stream.
"""

import asyncio
import pytest
from datetime import datetime, timezone
from edge.models import CanonicalTelemetry, CanonicalSource, CanonicalState, EventType, QualityCode
from storage.database import get_engine, get_session_factory, init_db
from storage.repository import TelemetryRepository
from api.dependencies import get_factory_profiles
from api.services.realtime_service import RealtimeService


@pytest.mark.asyncio
async def test_realtime_service_event_generator():
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    repo = TelemetryRepository(session_factory)
    profiles = get_factory_profiles()

    service = RealtimeService(repository=repo, profiles=profiles, interval_seconds=0.1)

    # Insert a new record
    now_str = datetime.now(timezone.utc).isoformat()
    c = CanonicalTelemetry(
        schema_version="1.0.0",
        event_id="evt_rt_1",
        event_type=EventType.TELEMETRY,
        plant_id="PLANT_01",
        line_id="LINE_A",
        machine_id="CNC-001",
        machine_type="CNC_MACHINING_CENTER",
        source=CanonicalSource("OPC_UA", "127.0.0.1:4840", "ns=2;s=CNC-001"),
        event_time=now_str,
        ingestion_time=now_str,
        sequence=1,
        state=CanonicalState("RUNNING", "HEALTHY"),
        quality=QualityCode.GOOD,
        measurements={"spindle_speed_rpm": 9200.0}
    )
    repo.insert(c)

    gen = service.event_generator()
    first_event = await anext(gen)
    assert "data: " in first_event
    assert "CNC-001" in first_event
    assert "9200.0" in first_event
