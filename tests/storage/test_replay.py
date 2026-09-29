"""
Unit tests for ReplayWorker and exponential backoff retry.
"""

from edge.models import CanonicalTelemetry, CanonicalSource, CanonicalState, EventType, QualityCode
from storage.buffer import PersistentBuffer
from storage.database import get_engine, get_session_factory, init_db
from storage.repository import TelemetryRepository
from storage.replay import ReplayWorker


def test_replay_worker_replays_to_repository(tmp_path):
    db_path = tmp_path / "test_replay_db.db"
    engine = get_engine(f"sqlite:///{db_path}")
    init_db(engine)
    session_factory = get_session_factory(engine)
    repo = TelemetryRepository(session_factory)

    buffer_path = str(tmp_path / "test_replay_buffer.db")
    buffer = PersistentBuffer(buffer_path)

    # Prepare canonical event and buffer it
    c = CanonicalTelemetry(
        schema_version="1.0.0",
        event_id="evt_replay_1",
        event_type=EventType.TELEMETRY,
        plant_id="PLANT_01",
        line_id="LINE_A",
        machine_id="CNC-001",
        machine_type="CNC_MACHINING_CENTER",
        source=CanonicalSource("OPC_UA", "", "ns=2;s=CNC-001"),
        event_time="2026-09-28T12:00:00Z",
        ingestion_time="2026-09-28T12:00:00Z",
        sequence=1,
        state=CanonicalState("RUNNING", "HEALTHY"),
        quality=QualityCode.GOOD,
        measurements={"spindle_speed_rpm": 9000.0}
    )

    import json
    buffer.add_event(c.event_id, c.machine_id, c.sequence, "topic/canonical", json.dumps(c.to_dict()))
    assert buffer.count_by_status("PENDING") == 1

    # Replay worker processes batch
    worker = ReplayWorker(buffer=buffer, repository=repo)
    replayed = worker.replay_batch()
    assert replayed == 1
    assert buffer.count_by_status("PENDING") == 0

    # Verify repository has the record
    stored = repo.get_by_event_id("evt_replay_1")
    assert stored is not None
    assert stored.machine_id == "CNC-001"
