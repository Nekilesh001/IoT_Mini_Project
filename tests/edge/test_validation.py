"""
Unit tests for machine-aware telemetry validation.
"""

from simulator.runtime.factory_runtime import FactorySimulator
from protocols.models import ProtocolReading, ProtocolType
from edge.validation import TelemetryValidator
from edge.models import QualityCode


def test_validation_valid_reading():
    factory = FactorySimulator(seed=42)
    profiles = {m.machine_id: m.profile for m in factory.get_all_machines()}
    cnc_profile = profiles["CNC-001"]

    valid_reading = ProtocolReading(
        machine_id="CNC-001",
        machine_type="CNC_MACHINING_CENTER",
        protocol=ProtocolType.OPC_UA,
        timestamp="2026-09-28T12:00:00Z",
        sequence=1,
        measurements={
            "spindle_speed_rpm": 9000.0,
            "spindle_load_pct": 70.0,
            "spindle_temperature_c": 45.0,
            "vibration_rms_mm_s": 1.5,
            "feed_rate_mm_min": 1200.0,
            "coolant_pressure_bar": 5.0,
            "tool_wear_index_pct": 10.0,
            "axis_x_position_mm": 100.0,
            "axis_y_position_mm": 150.0,
            "axis_z_position_mm": 50.0
        },
        source_address="ns=2;s=CNC-001",
        raw_payload={}
    )

    res = TelemetryValidator.validate_reading(valid_reading, cnc_profile)
    assert res.is_valid
    assert len(res.errors) == 0


def test_validation_unknown_machine_profile():
    valid_reading = ProtocolReading(
        machine_id="UNKNOWN-999",
        machine_type="CNC_MACHINING_CENTER",
        protocol=ProtocolType.OPC_UA,
        timestamp="2026-09-28T12:00:00Z",
        sequence=1,
        measurements={},
        source_address="",
        raw_payload={}
    )
    res = TelemetryValidator.validate_reading(valid_reading, None)
    assert not res.is_valid
    assert "Unknown machine_id" in res.errors[0]


def test_validation_datatype_and_range_failure():
    factory = FactorySimulator(seed=42)
    profiles = {m.machine_id: m.profile for m in factory.get_all_machines()}
    cnc_profile = profiles["CNC-001"]

    bad_reading = ProtocolReading(
        machine_id="CNC-001",
        machine_type="CNC_MACHINING_CENTER",
        protocol=ProtocolType.OPC_UA,
        timestamp="2026-09-28T12:00:00Z",
        sequence=1,
        measurements={
            "spindle_speed_rpm": "not_a_number",  # Type failure
            "spindle_temperature_c": 9999.0        # Range failure
        },
        source_address="ns=2;s=CNC-001",
        raw_payload={}
    )

    res = TelemetryValidator.validate_reading(bad_reading, cnc_profile)
    assert not res.is_valid
    assert res.signal_qualities.get("spindle_speed_rpm") == QualityCode.BAD
    assert res.signal_qualities.get("spindle_temperature_c") == QualityCode.OUT_OF_RANGE
