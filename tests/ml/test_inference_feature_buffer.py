"""
Unit tests for MachineTelemetryBuffer and TemporalFeatureBuffer.
"""

from datetime import datetime, timezone
import pytest

from edge.models import CanonicalTelemetry, CanonicalSource, CanonicalState, EventType, QualityCode
from ml.inference.errors import InvalidTelemetryError
from ml.inference.feature_buffer import TemporalFeatureBuffer, MachineTelemetryBuffer


def create_sample_telemetry(machine_id: str, seq: int, temp: float = 45.0) -> CanonicalTelemetry:
    return CanonicalTelemetry(
        event_id=f"EVT-{machine_id}-{seq:04d}",
        schema_version="1.0.0",
        event_type=EventType.TELEMETRY,
        plant_id="PLANT_01",
        line_id="LINE_A",
        machine_id=machine_id,
        machine_type="CNC_MACHINE",
        source=CanonicalSource(protocol="OPC_UA", endpoint="opc.tcp://localhost:4840", source_address="ns=2;s=CNC"),
        event_time=f"2026-01-01T08:00:{seq:02d}+00:00",
        ingestion_time="2026-01-01T08:00:00+00:00",
        sequence=seq,
        state=CanonicalState(operating="RUNNING", health="HEALTHY"),
        quality=QualityCode.GOOD,
        measurements={"spindle_temperature_c": temp, "spindle_speed_rpm": 1200.0},
    )


def test_buffer_warmup_and_sample_count():
    buf = MachineTelemetryBuffer(machine_id="CNC-001", max_size=10, min_warmup=3)
    assert not buf.is_ready

    # Add 2 observations -> not ready
    buf.add(create_sample_telemetry("CNC-001", 1))
    buf.add(create_sample_telemetry("CNC-001", 2))
    assert not buf.is_ready
    assert buf.sample_count == 2

    # Add 3rd observation -> ready
    buf.add(create_sample_telemetry("CNC-001", 3))
    assert buf.is_ready
    assert buf.sample_count == 3


def test_buffer_duplicate_event_rejection():
    buf = MachineTelemetryBuffer(machine_id="CNC-001", max_size=10, min_warmup=3)
    t1 = create_sample_telemetry("CNC-001", 1)

    assert buf.add(t1) is True
    assert buf.add(t1) is False  # Duplicate event_id rejected
    assert buf.sample_count == 1


def test_buffer_machine_id_mismatch_error():
    buf = MachineTelemetryBuffer(machine_id="CNC-001", max_size=10, min_warmup=3)
    t_other = create_sample_telemetry("ROBOT-001", 1)

    with pytest.raises(InvalidTelemetryError):
        buf.add(t_other)


def test_temporal_feature_buffer_fleet_management():
    fleet_buf = TemporalFeatureBuffer(max_buffer_size=20, min_warmup_samples=3)

    t_cnc = create_sample_telemetry("CNC-001", 1)
    t_rob = create_sample_telemetry("ROB-001", 1)

    fleet_buf.add_telemetry(t_cnc)
    fleet_buf.add_telemetry(t_rob)

    assert set(fleet_buf.get_all_machine_ids()) == {"CNC-001", "ROB-001"}
    assert not fleet_buf.is_machine_ready("CNC-001")

    # Feed CNC-001 to ready
    fleet_buf.add_telemetry(create_sample_telemetry("CNC-001", 2))
    fleet_buf.add_telemetry(create_sample_telemetry("CNC-001", 3))

    assert fleet_buf.is_machine_ready("CNC-001")
    assert not fleet_buf.is_machine_ready("ROB-001")

    df = fleet_buf.get_machine_dataframe("CNC-001")
    assert len(df) == 3
    assert "spindle_temperature_c" in df.columns
