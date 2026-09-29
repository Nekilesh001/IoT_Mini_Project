import os
import tempfile
import json
import pytest
from datetime import datetime, timezone
from edge.models import CanonicalTelemetry, CanonicalSource, CanonicalState, EventType, QualityCode
from storage.database import get_engine, get_session_factory, init_db
from storage.repository import TelemetryRepository
from event_bus.publisher import CanonicalTelemetryPublisher
from event_bus.consumer import CanonicalTelemetryConsumer

def _create_sample_canonical(machine_id="CNC-001", seq=1):
    now_str = datetime.now(timezone.utc).isoformat()
    return CanonicalTelemetry(
        schema_version="1.0.0",
        event_id=f"evt-{machine_id}-{seq}",
        event_type=EventType.TELEMETRY,
        plant_id="PLANT_01",
        line_id="LINE_A",
        machine_id=machine_id,
        machine_type="CNC_MILLING",
        source=CanonicalSource(protocol="MODBUS_TCP", endpoint="127.0.0.1:5020", source_address="1"),
        event_time=now_str,
        ingestion_time=now_str,
        sequence=seq,
        state=CanonicalState(operating="RUNNING", health="HEALTHY"),
        quality=QualityCode.GOOD,
        measurements={"spindle_speed": 1200.0, "vibration": 0.45},
        derived={"power_kw": 4.2},
        ml={"anomaly_score": 0.01}
    )

def test_consumer_receives_and_persists():
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    repo = TelemetryRepository(session_factory)

    pub = CanonicalTelemetryPublisher()
    pub.connect()

    consumer = CanonicalTelemetryConsumer(repository=repo)
    consumer.start()

    canonical = _create_sample_canonical("CNC-001", 1)
    pub.publish(canonical)

    # Verify persistence
    record = repo.get_latest_by_machine("CNC-001")
    assert record is not None
    assert record.event_id == "evt-CNC-001-1"
    assert record.measurements["spindle_speed"] == 1200.0

    metrics = consumer.get_metrics()
    assert metrics["consumed_count"] == 1
    assert metrics["persisted_count"] == 1
    assert metrics["duplicate_count"] == 0

    consumer.stop()
    pub.disconnect()

def test_consumer_handles_duplicate_message_cleanly():
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    repo = TelemetryRepository(session_factory)

    pub = CanonicalTelemetryPublisher()
    pub.connect()

    consumer = CanonicalTelemetryConsumer(repository=repo)
    consumer.start()

    canonical = _create_sample_canonical("CNC-001", 1)
    # Publish twice
    pub.publish(canonical)
    pub.publish(canonical)

    assert repo.count_by_machine("CNC-001") == 1
    metrics = consumer.get_metrics()
    assert metrics["consumed_count"] == 2
    assert metrics["persisted_count"] == 1
    assert metrics["duplicate_count"] == 1

    consumer.stop()
    pub.disconnect()

def test_consumer_handles_malformed_json_safely():
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    repo = TelemetryRepository(session_factory)

    consumer = CanonicalTelemetryConsumer(repository=repo)
    consumer.start()

    # Pass malformed message directly to callback
    consumer._on_message("factory/PLANT_01/LINE_A/CNC-001/telemetry/canonical", "not valid json {{{")

    metrics = consumer.get_metrics()
    assert metrics["consumed_count"] == 1
    assert metrics["failed_count"] == 1
    assert metrics["persisted_count"] == 0
    assert repo.count_by_machine("CNC-001") == 0

    consumer.stop()
