"""
Dedicated verification script testing Phase 4 persistence, queries, and buffering against a real live PostgreSQL database.
"""

from datetime import datetime, timezone, timedelta
import sys

from edge.models import (
    CanonicalTelemetry,
    CanonicalSource,
    CanonicalState,
    EventType,
    QualityCode,
    IngestionStatus,
)
from edge.service import EdgeIngestionService
from protocols.models import ProtocolReading, ProtocolType
from simulator.runtime.factory_runtime import FactorySimulator
from storage.database import get_engine, get_session_factory, init_db
from storage.repository import TelemetryRepository
from storage.buffer import PersistentBuffer
from storage.replay import ReplayWorker
from event_bus.publisher import CanonicalTelemetryPublisher
from event_bus.consumer import CanonicalTelemetryConsumer


def run_postgres_verification(postgres_url: str):
    print("=" * 80)
    print(" REAL POSTGRESQL LIVE VERIFICATION SUITE")
    print(f" Target Database URL: {postgres_url.split('@')[-1]}")
    print("=" * 80)

    # 1. Initialize Real PostgreSQL Engine and Tables
    print("\n[1] Initializing SQLAlchemy engine and creating PostgreSQL tables...")
    engine = get_engine(postgres_url)
    init_db(engine)
    session_factory = get_session_factory(engine)
    repo = TelemetryRepository(session_factory)
    print(" -> Schema 'telemetry_records' with JSONB created successfully on PostgreSQL.")

    # 2. Insert & Validate Heterogeneous Records
    print("\n[2] Testing CRUD & Heterogeneous Machine Measurements with native PostgreSQL JSONB...")
    now = datetime.now(timezone.utc)

    # (a) CNC Machining Center (OPC UA)
    cnc = CanonicalTelemetry(
        schema_version="1.0.0",
        event_id="evt_pg_cnc_1",
        event_type=EventType.TELEMETRY,
        plant_id="PLANT_01",
        line_id="LINE_A",
        machine_id="CNC-001",
        machine_type="CNC_MACHINING_CENTER",
        source=CanonicalSource(protocol="OPC_UA", endpoint="opc.tcp://127.0.0.1:4840", source_address="ns=2;s=CNC-001"),
        event_time=(now - timedelta(seconds=20)).isoformat(),
        ingestion_time=(now - timedelta(seconds=20)).isoformat(),
        sequence=1,
        state=CanonicalState(operating="RUNNING", health="HEALTHY"),
        quality=QualityCode.GOOD,
        measurements={"spindle_speed_rpm": 9200.0, "spindle_load_pct": 68.0, "vibration_rms_mm_s": 0.92},
        derived={"power_kw": 11.2},
        ml={"anomaly_score": 0.02}
    )

    # (b) Autonomous Mobile Robot (MQTT)
    agv = CanonicalTelemetry(
        schema_version="1.0.0",
        event_id="evt_pg_agv_1",
        event_type=EventType.TELEMETRY,
        plant_id="PLANT_01",
        line_id="LINE_A",
        machine_id="AGV-001",
        machine_type="AUTONOMOUS_MOBILE_ROBOT",
        source=CanonicalSource(protocol="MQTT", endpoint="127.0.0.1:1883", source_address="factory/PLANT_01/LINE_A/AGV-001/telemetry"),
        event_time=(now - timedelta(seconds=10)).isoformat(),
        ingestion_time=(now - timedelta(seconds=10)).isoformat(),
        sequence=1,
        state=CanonicalState(operating="RUNNING", health="HEALTHY"),
        quality=QualityCode.GOOD,
        measurements={"battery_soc_pct": 92.0, "battery_voltage_v": 49.1, "pos_x_m": 12.0, "pos_y_m": 24.5},
        derived={},
        ml={}
    )

    # (c) Industrial Chiller (Modbus TCP)
    chl = CanonicalTelemetry(
        schema_version="1.0.0",
        event_id="evt_pg_chl_1",
        event_type=EventType.TELEMETRY,
        plant_id="PLANT_01",
        line_id="LINE_A",
        machine_id="CHL-001",
        machine_type="INDUSTRIAL_CHILLER",
        source=CanonicalSource(protocol="MODBUS_TCP", endpoint="127.0.0.1:5020", source_address="127.0.0.1:5020/unit=12"),
        event_time=now.isoformat(),
        ingestion_time=now.isoformat(),
        sequence=1,
        state=CanonicalState(operating="RUNNING", health="HEALTHY"),
        quality=QualityCode.GOOD,
        measurements={"supply_water_temp_c": 7.2, "return_water_temp_c": 12.4, "cop": 4.8},
        derived={"delta_t_c": 5.2},
        ml={}
    )

    # Insert into real PostgreSQL
    assert repo.insert(cnc) is True
    assert repo.insert(agv) is True
    assert repo.insert(chl) is True
    print(" -> Successfully inserted 3 heterogeneous machine records into PostgreSQL.")

    # 3. Query Verifications
    print("\n[3] Verifying PostgreSQL queries (Latest, History, Counts, Time-Range)...")
    # Latest record
    latest_cnc = repo.get_latest_by_machine("CNC-001")
    assert latest_cnc is not None
    assert latest_cnc.measurements["spindle_speed_rpm"] == 9200.0
    print(f" -> get_latest_by_machine('CNC-001'): Spindle Speed = {latest_cnc.measurements['spindle_speed_rpm']} RPM")

    # Counts
    assert repo.count_by_machine("CNC-001") >= 1
    assert repo.count_by_machine("AGV-001") >= 1
    assert repo.count_by_machine("CHL-001") >= 1
    print(f" -> count_by_machine: CNC-001={repo.count_by_machine('CNC-001')}, AGV-001={repo.count_by_machine('AGV-001')}, CHL-001={repo.count_by_machine('CHL-001')}")

    # Time-Range Query
    start_time = now - timedelta(seconds=30)
    end_time = now + timedelta(seconds=5)
    time_results = repo.query_time_range("CNC-001", start_time, end_time)
    assert len(time_results) >= 1
    print(f" -> query_time_range on PostgreSQL returned {len(time_results)} record(s).")

    # 4. Idempotency & Duplicate Safety on PostgreSQL
    print("\n[4] Testing Idempotent Conflict Handling on PostgreSQL...")
    dup_insert_same_event = repo.insert(cnc)
    print(f" -> Re-inserting exact event_id: {dup_insert_same_event} (False indicates clean duplicate rejection)")
    assert dup_insert_same_event is False

    dup_seq_different_event = CanonicalTelemetry(
        schema_version="1.0.0",
        event_id="evt_pg_cnc_conflict",
        event_type=EventType.TELEMETRY,
        plant_id="PLANT_01",
        line_id="LINE_A",
        machine_id="CNC-001",
        machine_type="CNC_MACHINING_CENTER",
        source=CanonicalSource(protocol="OPC_UA", endpoint="opc.tcp://127.0.0.1:4840", source_address="ns=2;s=CNC-001"),
        event_time=now.isoformat(),
        ingestion_time=now.isoformat(),
        sequence=1,  # Duplicate sequence for CNC-001
        state=CanonicalState(operating="RUNNING", health="HEALTHY"),
        quality=QualityCode.GOOD,
        measurements={"spindle_speed_rpm": 9200.0}
    )
    dup_insert_seq = repo.insert(dup_seq_different_event)
    print(f" -> Re-inserting same (machine_id, sequence) with different event_id: {dup_insert_seq} (False confirms duplicate protection)")
    assert dup_insert_seq is False

    # 5. Outage, SQLite Persistent Buffer Fallback & Replay into PostgreSQL
    print("\n[5] Testing Outage, SQLite Store-and-Forward Buffer & Replay into PostgreSQL...")
    buffer = PersistentBuffer("postgres_test_buffer.db")
    buffer.clear()

    pub = CanonicalTelemetryPublisher(buffer=buffer)
    pub.connect()

    consumer = CanonicalTelemetryConsumer(repository=repo)
    consumer.start()

    # Simulate broker outage
    pub.simulate_broker_outage()
    c_outage = CanonicalTelemetry(
        schema_version="1.0.0",
        event_id="evt_pg_outage_1",
        event_type=EventType.TELEMETRY,
        plant_id="PLANT_01",
        line_id="LINE_A",
        machine_id="CNC-002",
        machine_type="CNC_LATHE",
        source=CanonicalSource(protocol="MODBUS_TCP", endpoint="127.0.0.1:5020", source_address="127.0.0.1:5020/unit=2"),
        event_time=now.isoformat(),
        ingestion_time=now.isoformat(),
        sequence=99,
        state=CanonicalState(operating="RUNNING", health="HEALTHY"),
        quality=QualityCode.GOOD,
        measurements={"spindle_speed_rpm": 2400.0, "vibration_rms_mm_s": 0.65}
    )
    assert pub.publish(c_outage) is False
    assert buffer.count_by_status("PENDING") == 1
    print(" -> Outage correctly stored event in SQLite persistent buffer. Pending buffer count = 1")

    # Restore broker and trigger replay worker into PostgreSQL
    pub.restore_broker()
    worker = ReplayWorker(buffer=buffer, publisher=pub, batch_size=10)
    replayed = worker.replay_batch()
    assert replayed == 1
    assert buffer.count_by_status("PENDING") == 0
    print(" -> Replay worker drained buffer (Pending count = 0).")

    # Verify event reached PostgreSQL
    persisted_outage_rec = repo.get_by_event_id("evt_pg_outage_1")
    assert persisted_outage_rec is not None
    assert persisted_outage_rec.machine_id == "CNC-002"
    assert persisted_outage_rec.sequence == 99
    print(f" -> Verified recovered event persisted in PostgreSQL: machine={persisted_outage_rec.machine_id}, seq={persisted_outage_rec.sequence}")

    consumer.stop()
    pub.disconnect()
    engine.dispose()
    buffer.clear()

    print("\n" + "=" * 80)
    print(" REAL POSTGRESQL VERIFICATION COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    db_url = "postgresql://postgres:neki132506@127.0.0.1:5432/smart_factory"
    run_postgres_verification(db_url)
