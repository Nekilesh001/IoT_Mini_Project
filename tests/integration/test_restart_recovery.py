"""
Integration test verifying durable store-and-forward buffer survival across process restart and recovery.
"""

import os
import json
import tempfile
import pytest
from datetime import datetime, timezone

from edge.models import CanonicalTelemetry, CanonicalSource, CanonicalState, EventType, QualityCode
from storage.database import get_engine, get_session_factory, init_db
from storage.repository import TelemetryRepository
from storage.buffer import PersistentBuffer, BufferStatus
from storage.replay import ReplayWorker


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


def test_buffer_survives_restart_and_replays_cleanly():
    with tempfile.TemporaryDirectory() as tmpdir:
        buffer_file = os.path.join(tmpdir, "durable_buffer.db")

        # 1. First process life: buffer some events during outage
        buf_proc1 = PersistentBuffer(buffer_file)
        c1 = _create_sample_canonical("CNC-001", 1)
        c2 = _create_sample_canonical("CNC-001", 2)
        c3 = _create_sample_canonical("CNC-001", 3)

        buf_proc1.add_event(c1.event_id, c1.machine_id, c1.sequence, "topic/1", json.dumps(c1.to_dict()))
        buf_proc1.add_event(c2.event_id, c2.machine_id, c2.sequence, "topic/2", json.dumps(c2.to_dict()))
        buf_proc1.add_event(c3.event_id, c3.machine_id, c3.sequence, "topic/3", json.dumps(c3.to_dict()))

        assert len(buf_proc1.get_pending_events()) == 3

        # 2. Simulate process termination / crash
        del buf_proc1

        # 3. Second process life: new instance recovers from existing SQLite file
        buf_proc2 = PersistentBuffer(buffer_file)
        pending = buf_proc2.get_pending_events()
        assert len(pending) == 3
        assert [e.sequence for e in pending] == [1, 2, 3]

        # 4. Initialize repository and replay
        engine = get_engine("sqlite:///:memory:")
        init_db(engine)
        session_factory = get_session_factory(engine)
        repo = TelemetryRepository(session_factory)

        worker = ReplayWorker(buffer=buf_proc2, repository=repo, batch_size=10)
        replayed = worker.replay_batch()
        assert replayed == 3

        # 5. Confirm repository persisted all 3 and buffer has 0 pending
        assert repo.count_by_machine("CNC-001") == 3
        assert len(buf_proc2.get_pending_events()) == 0
