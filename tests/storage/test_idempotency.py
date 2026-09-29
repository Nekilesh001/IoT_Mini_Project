"""
Unit tests for idempotent and duplicate-safe database persistence.
"""

from edge.models import CanonicalTelemetry, CanonicalSource, CanonicalState, EventType, QualityCode
from storage.database import get_engine, get_session_factory, init_db
from storage.repository import TelemetryRepository


def test_repository_duplicate_insert_handling(tmp_path):
    db_path = tmp_path / "test_idempotency.db"
    engine = get_engine(f"sqlite:///{db_path}")
    init_db(engine)
    session_factory = get_session_factory(engine)
    repo = TelemetryRepository(session_factory)

    c = CanonicalTelemetry(
        schema_version="1.0.0",
        event_id="evt_idem_1",
        event_type=EventType.TELEMETRY,
        plant_id="PLANT_01",
        line_id="LINE_A",
        machine_id="CNC-002",
        machine_type="CNC_LATHE",
        source=CanonicalSource("MODBUS_TCP", "", "127.0.0.1:5020"),
        event_time="2026-09-28T12:00:00Z",
        ingestion_time="2026-09-28T12:00:00Z",
        sequence=1,
        state=CanonicalState("RUNNING", "HEALTHY"),
        quality=QualityCode.GOOD,
        measurements={"spindle_speed_rpm": 2500.0}
    )

    # First insert succeeds
    first_res = repo.insert(c)
    assert first_res is True

    # Duplicate insert with same event_id and (machine_id, sequence) returns False without crashing
    second_res = repo.insert(c)
    assert second_res is False

    # Distinct event_id but identical (machine_id, sequence) is also rejected as duplicate
    c_duplicate_seq = CanonicalTelemetry(
        schema_version="1.0.0",
        event_id="evt_idem_2",  # Different event_id
        event_type=EventType.TELEMETRY,
        plant_id="PLANT_01",
        line_id="LINE_A",
        machine_id="CNC-002",
        machine_type="CNC_LATHE",
        source=CanonicalSource("MODBUS_TCP", "", "127.0.0.1:5020"),
        event_time="2026-09-28T12:00:01Z",
        ingestion_time="2026-09-28T12:00:01Z",
        sequence=1,  # Same machine_id + sequence
        state=CanonicalState("RUNNING", "HEALTHY"),
        quality=QualityCode.GOOD,
        measurements={"spindle_speed_rpm": 2500.0}
    )
    dup_seq_res = repo.insert(c_duplicate_seq)
    assert dup_seq_res is False

    # Confirm only 1 record exists
    assert repo.count_by_machine("CNC-002") == 1
