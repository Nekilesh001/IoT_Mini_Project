import os
import tempfile
import pytest
from datetime import datetime, timezone
from edge.models import CanonicalTelemetry, CanonicalSource, CanonicalState, EventType, QualityCode
from storage.buffer import PersistentBuffer
from event_bus.publisher import CanonicalTelemetryPublisher

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

def test_publisher_connect_and_publish():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_buffer.db")
        buf = PersistentBuffer(db_path)
        pub = CanonicalTelemetryPublisher(buffer=buf)
        pub.connect()
        assert pub.is_connected

        canonical = _create_sample_canonical("CNC-001", 1)
        success = pub.publish(canonical)
        assert success is True
        assert pub.get_metrics()["published_count"] == 1
        assert pub.get_metrics()["buffered_count"] == 0

def test_publisher_buffer_fallback_on_outage():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_buffer.db")
        buf = PersistentBuffer(db_path)
        pub = CanonicalTelemetryPublisher(buffer=buf)
        pub.connect()
        
        # Simulate broker outage
        pub.simulate_broker_outage()
        assert not pub.is_connected

        canonical = _create_sample_canonical("CNC-001", 2)
        success = pub.publish(canonical)
        assert success is False
        assert pub.get_metrics()["published_count"] == 0
        assert pub.get_metrics()["failed_count"] == 1
        assert pub.get_metrics()["buffered_count"] == 1

        # Check buffer contents
        pending = buf.get_pending_events()
        assert len(pending) == 1
        assert pending[0].event_id == "evt-CNC-001-2"
