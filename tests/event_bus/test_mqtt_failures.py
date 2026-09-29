import os
import tempfile
import pytest
from datetime import datetime, timezone
from edge.models import CanonicalTelemetry, CanonicalSource, CanonicalState, EventType, QualityCode
from storage.buffer import PersistentBuffer
from storage.database import get_engine, get_session_factory, init_db
from storage.repository import TelemetryRepository
from storage.replay import ReplayWorker
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

def test_mqtt_broker_outage_and_recovery_replay():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_buffer.db")
        buf = PersistentBuffer(db_path)

        engine = get_engine("sqlite:///:memory:")
        init_db(engine)
        session_factory = get_session_factory(engine)
        repo = TelemetryRepository(session_factory)

        pub = CanonicalTelemetryPublisher(buffer=buf)
        pub.connect()

        consumer = CanonicalTelemetryConsumer(repository=repo)
        consumer.start()

        # 1. Normal publish succeeds
        c1 = _create_sample_canonical("CNC-001", 1)
        assert pub.publish(c1) is True
        assert repo.count_by_machine("CNC-001") == 1
        assert len(buf.get_pending_events()) == 0

        # 2. Broker outage occurs
        pub.simulate_broker_outage()
        c2 = _create_sample_canonical("CNC-001", 2)
        c3 = _create_sample_canonical("CNC-001", 3)
        assert pub.publish(c2) is False
        assert pub.publish(c3) is False
        assert repo.count_by_machine("CNC-001") == 1  # Unchanged in DB
        assert len(buf.get_pending_events()) == 2     # Buffered

        # 3. Broker restored
        pub.restore_broker()

        # 4. Replay worker runs
        worker = ReplayWorker(buffer=buf, publisher=pub, batch_size=10)
        replayed = worker.replay_batch()
        assert replayed == 2

        # 5. DB now has all 3 records
        assert repo.count_by_machine("CNC-001") == 3
        assert len(buf.get_pending_events()) == 0

        consumer.stop()
        pub.disconnect()
