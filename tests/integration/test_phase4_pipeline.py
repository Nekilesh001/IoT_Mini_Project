"""
End-to-end integration test for Phase 4 pipeline.
Verifies Modbus TCP, OPC UA, and MQTT machine types flowing through:
EdgeIngestionService -> CanonicalTelemetry -> MQTT Publisher -> MQTT Consumer -> TelemetryRepository
"""

import pytest
from datetime import datetime, timezone

from simulator.runtime.factory_runtime import FactorySimulator
from protocols.models import ProtocolReading, ProtocolType
from edge.service import EdgeIngestionService
from edge.models import IngestionStatus
from storage.database import get_engine, get_session_factory, init_db
from storage.repository import TelemetryRepository
from event_bus.publisher import CanonicalTelemetryPublisher
from event_bus.consumer import CanonicalTelemetryConsumer


def test_full_heterogeneous_pipeline_end_to_end():
    # 1. Setup DB Repository
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = get_session_factory(engine)
    repo = TelemetryRepository(session_factory)

    # 2. Setup Phase 4 Event Bus
    pub = CanonicalTelemetryPublisher()
    pub.connect()

    consumer = CanonicalTelemetryConsumer(repository=repo)
    consumer.start()

    # 3. Setup Phase 3 Edge Ingestion Service
    factory = FactorySimulator(seed=42)
    profiles = {m.machine_id: m.profile for m in factory.get_all_machines()}
    edge_service = EdgeIngestionService(profiles=profiles)

    # 4. Generate 3 representative readings across 3 protocols
    # (a) Modbus: CNC Lathe (CNC-002)
    modbus_reading = ProtocolReading(
        machine_id="CNC-002",
        machine_type="CNC_LATHE",
        protocol=ProtocolType.MODBUS_TCP,
        timestamp=datetime.now(timezone.utc).isoformat(),
        sequence=1,
        measurements={
            "spindle_speed_rpm": 2400.0,
            "spindle_load_pct": 55.0,
            "spindle_temperature_c": 38.5,
            "vibration_rms_mm_s": 0.85,
            "feed_rate_mm_min": 750.0,
            "coolant_flow_l_min": 11.5,
            "operating_state": "RUNNING"
        },
        source_address="127.0.0.1:5020/unit=1",
        raw_payload=[0] * 13
    )

    # (b) OPC UA: CNC Machining Center (CNC-001)
    opcua_reading = ProtocolReading(
        machine_id="CNC-001",
        machine_type="CNC_MACHINING_CENTER",
        protocol=ProtocolType.OPC_UA,
        timestamp=datetime.now(timezone.utc).isoformat(),
        sequence=1,
        measurements={
            "spindle_speed_rpm": 9200.0,
            "spindle_load_pct": 68.0,
            "spindle_temperature_c": 44.0,
            "vibration_rms_mm_s": 0.92,
            "feed_rate_mm_min": 1200.0,
            "coolant_pressure_bar": 20.0,
            "tool_wear_pct": 10.0,
            "operating_state": "RUNNING"
        },
        source_address="opc.tcp://127.0.0.1:4840/freeopcua/server/",
        raw_payload={}
    )

    # (c) MQTT: Autonomous Mobile Robot (AGV-001)
    mqtt_reading = ProtocolReading(
        machine_id="AGV-001",
        machine_type="AUTONOMOUS_MOBILE_ROBOT",
        protocol=ProtocolType.MQTT,
        timestamp=datetime.now(timezone.utc).isoformat(),
        sequence=1,
        measurements={
            "battery_soc_pct": 92.0,
            "battery_voltage_v": 49.1,
            "battery_temp_c": 26.0,
            "pos_x_m": 12.0,
            "pos_y_m": 24.5,
            "heading_deg": 180.0,
            "operating_state": "RUNNING"
        },
        source_address="factory/PLANT_01/LINE_A/AGV-001/telemetry",
        raw_payload={}
    )

    # Ingest through Edge Service & Publish to Phase 4 Event Bus
    for reading in [modbus_reading, opcua_reading, mqtt_reading]:
        res = edge_service.ingest_reading(reading)
        assert res.status == IngestionStatus.ACCEPTED
        assert res.canonical_telemetry is not None
        pub_ok = pub.publish(res.canonical_telemetry)
        assert pub_ok is True

    # 5. Verify all 3 records persisted cleanly in repository
    assert repo.count_by_machine("CNC-002") == 1
    assert repo.count_by_machine("CNC-001") == 1
    assert repo.count_by_machine("AGV-001") == 1

    # Verify heterogeneous measurements are intact and distinct
    lathe_rec = repo.get_latest_by_machine("CNC-002")
    assert lathe_rec.measurements["spindle_speed_rpm"] == 2400.0
    assert "battery_soc_pct" not in lathe_rec.measurements

    machining_rec = repo.get_latest_by_machine("CNC-001")
    assert machining_rec.measurements["spindle_speed_rpm"] == 9200.0
    assert "battery_soc_pct" not in machining_rec.measurements

    agv_rec = repo.get_latest_by_machine("AGV-001")
    assert agv_rec.measurements["battery_soc_pct"] == 92.0
    assert "spindle_speed_rpm" not in agv_rec.measurements

    consumer.stop()
    pub.disconnect()
