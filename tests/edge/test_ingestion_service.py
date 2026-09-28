"""
Unit and integration tests for EdgeIngestionService.
"""

from simulator.runtime.factory_runtime import FactorySimulator
from protocols.models import ProtocolReading, ProtocolType
from edge.service import EdgeIngestionService
from edge.models import IngestionStatus, QualityCode


def test_edge_ingestion_service_pipeline():
    factory = FactorySimulator(seed=42)
    profiles = {m.machine_id: m.profile for m in factory.get_all_machines()}
    service = EdgeIngestionService(profiles=profiles)

    reading = ProtocolReading(
        machine_id="CNC-002",
        machine_type="CNC_LATHE",
        protocol=ProtocolType.MODBUS_TCP,
        timestamp="2026-09-28T12:00:00Z",
        sequence=1,
        measurements={
            "spindle_speed_rpm": 2500.0,
            "spindle_load_pct": 65.0,
            "spindle_temperature_c": 42.0,
            "vibration_rms_mm_s": 1.2,
            "feed_rate_mm_min": 800.0,
            "coolant_flow_l_min": 12.0,
            "operating_state": "RUNNING"
        },
        source_address="127.0.0.1:5020/unit=1",
        raw_payload=[0]*13
    )

    res = service.ingest_reading(reading)
    assert res.status == IngestionStatus.ACCEPTED
    assert res.canonical_telemetry is not None

    canonical = res.canonical_telemetry
    assert canonical.machine_id == "CNC-002"
    assert canonical.machine_type == "CNC_LATHE"
    assert canonical.source.protocol == "MODBUS_TCP"
    assert canonical.state.operating == "RUNNING"
    assert canonical.sequence == 1
    assert "operating_state" not in canonical.measurements
    assert "spindle_speed_rpm" in canonical.measurements
    assert "estimated_spindle_power_kw" in canonical.derived


def test_edge_ingestion_heterogeneous_preservation():
    factory = FactorySimulator(seed=42)
    profiles = {m.machine_id: m.profile for m in factory.get_all_machines()}
    service = EdgeIngestionService(profiles=profiles)

    # AGV-001 reading
    agv_reading = ProtocolReading(
        machine_id="AGV-001",
        machine_type="AUTONOMOUS_MOBILE_ROBOT",
        protocol=ProtocolType.MQTT,
        timestamp="2026-09-28T12:00:00Z",
        sequence=1,
        measurements={
            "battery_soc_pct": 88.0,
            "battery_voltage_v": 48.2,
            "battery_temp_c": 28.5,
            "pos_x_m": 14.5,
            "pos_y_m": 32.0,
            "heading_deg": 90.0,
            "operating_state": "RUNNING"
        },
        source_address="factory/PLANT_01/LINE_A/AGV-001/telemetry",
        raw_payload={}
    )

    res = service.ingest_reading(agv_reading)
    assert res.status == IngestionStatus.ACCEPTED
    assert "battery_soc_pct" in res.canonical_telemetry.measurements
    assert "pos_x_m" in res.canonical_telemetry.measurements
    assert "spindle_speed_rpm" not in res.canonical_telemetry.measurements
