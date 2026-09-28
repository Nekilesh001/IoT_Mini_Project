"""
Unit tests for CanonicalTelemetry schema and serialization models.
"""

import json
from edge.models import CanonicalTelemetry, CanonicalSource, CanonicalState, EventType, QualityCode


def test_canonical_model_serialization_and_deserialization():
    source = CanonicalSource(protocol="OPC_UA", endpoint="opc.tcp://127.0.0.1:4840", source_address="ns=2;s=CNC-001")
    state = CanonicalState(operating="RUNNING", health="HEALTHY")
    
    canonical = CanonicalTelemetry(
        schema_version="1.0.0",
        event_id="evt_test_12345",
        event_type=EventType.TELEMETRY,
        plant_id="PLANT_01",
        line_id="LINE_A",
        machine_id="CNC-001",
        machine_type="CNC_MACHINING_CENTER",
        source=source,
        event_time="2026-09-28T12:00:00Z",
        ingestion_time="2026-09-28T12:00:00.050Z",
        sequence=42,
        state=state,
        quality=QualityCode.GOOD,
        measurements={"spindle_speed_rpm": 9000.0, "spindle_load_pct": 75.0},
        derived={"estimated_spindle_power_kw": 11.25},
        ml={}
    )

    data_dict = canonical.to_dict()
    assert data_dict["schemaVersion"] == "1.0.0"
    assert data_dict["eventId"] == "evt_test_12345"
    assert data_dict["eventType"] == "TELEMETRY"
    assert data_dict["machineId"] == "CNC-001"
    assert data_dict["source"]["protocol"] == "OPC_UA"
    assert data_dict["source"]["sourceAddress"] == "ns=2;s=CNC-001"
    assert data_dict["sequence"] == 42
    assert data_dict["state"]["operating"] == "RUNNING"
    assert data_dict["quality"] == "GOOD"
    assert data_dict["measurements"]["spindle_speed_rpm"] == 9000.0
    assert data_dict["derived"]["estimated_spindle_power_kw"] == 11.25

    # JSON serialization check
    json_str = json.dumps(data_dict)
    assert "schemaVersion" in json_str

    # Deserialization check
    reconstructed = CanonicalTelemetry.from_dict(json.loads(json_str))
    assert reconstructed.machine_id == canonical.machine_id
    assert reconstructed.sequence == canonical.sequence
    assert reconstructed.quality == canonical.quality
