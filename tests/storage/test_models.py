"""
Unit tests for TelemetryRecord ORM model.
"""

from datetime import datetime, timezone
from storage.database import get_engine, get_session_factory, init_db
from storage.models import TelemetryRecord


def test_telemetry_record_orm_mapping(tmp_path):
    db_path = tmp_path / "test_models.db"
    engine = get_engine(f"sqlite:///{db_path}")
    init_db(engine)
    session_factory = get_session_factory(engine)

    now = datetime.now(timezone.utc)
    record = TelemetryRecord(
        event_id="evt_orm_1",
        schema_version="1.0.0",
        event_type="TELEMETRY",
        plant_id="PLANT_01",
        line_id="LINE_A",
        machine_id="CNC-001",
        machine_type="CNC_MACHINING_CENTER",
        protocol="OPC_UA",
        endpoint="opc.tcp://127.0.0.1:4840",
        source_address="ns=2;s=CNC-001",
        event_time=now,
        ingestion_time=now,
        sequence=1,
        operating_state="RUNNING",
        health_state="HEALTHY",
        quality="GOOD",
        measurements={"spindle_speed_rpm": 9000.0},
        derived={"power_kw": 11.2},
        ml={}
    )

    with session_factory() as session:
        session.add(record)
        session.commit()

        retrieved = session.get(TelemetryRecord, "evt_orm_1")
        assert retrieved is not None
        assert retrieved.machine_id == "CNC-001"
        assert retrieved.measurements["spindle_speed_rpm"] == 9000.0
        assert retrieved.derived["power_kw"] == 11.2
        assert retrieved.to_dict()["eventId"] == "evt_orm_1"
