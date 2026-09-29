"""
Unit tests for TelemetryRepository queries.
"""

from datetime import datetime, timezone, timedelta
from edge.models import CanonicalTelemetry, CanonicalSource, CanonicalState, EventType, QualityCode
from storage.database import get_engine, get_session_factory, init_db
from storage.repository import TelemetryRepository


def test_repository_insert_and_queries(tmp_path):
    db_path = tmp_path / "test_repo.db"
    engine = get_engine(f"sqlite:///{db_path}")
    init_db(engine)
    session_factory = get_session_factory(engine)
    repo = TelemetryRepository(session_factory)

    base_time = datetime.now(timezone.utc)

    # Insert 3 records for CNC-001
    for seq in range(1, 4):
        t_str = (base_time + timedelta(seconds=seq)).isoformat()
        c = CanonicalTelemetry(
            schema_version="1.0.0",
            event_id=f"evt_cnc_{seq}",
            event_type=EventType.TELEMETRY,
            plant_id="PLANT_01",
            line_id="LINE_A",
            machine_id="CNC-001",
            machine_type="CNC_MACHINING_CENTER",
            source=CanonicalSource("OPC_UA", "", "ns=2;s=CNC-001"),
            event_time=t_str,
            ingestion_time=t_str,
            sequence=seq,
            state=CanonicalState("RUNNING", "HEALTHY"),
            quality=QualityCode.GOOD,
            measurements={"spindle_speed_rpm": 9000.0 + seq}
        )
        assert repo.insert(c)

    # 1. Count
    assert repo.count_by_machine("CNC-001") == 3

    # 2. Get latest
    latest = repo.get_latest_by_machine("CNC-001")
    assert latest is not None
    assert latest.sequence == 3

    # 3. Get history
    history = repo.get_machine_history("CNC-001", limit=10)
    assert len(history) == 3

    # 4. Time range query
    start_t = base_time + timedelta(seconds=1.5)
    end_t = base_time + timedelta(seconds=3.5)
    in_range = repo.query_time_range("CNC-001", start_t, end_t)
    assert len(in_range) == 2
    assert [r.sequence for r in in_range] == [2, 3]
