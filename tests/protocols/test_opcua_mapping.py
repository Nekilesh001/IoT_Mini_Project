"""
Unit tests for OPC UA NodeID string generation and variant type mapping.
"""

from asyncua import ua
from simulator.core.domain import SignalType
from protocols.opcua.mapping import OPCUAMapper


def test_opcua_node_id_string_format():
    node_str = OPCUAMapper.get_node_id_string("PLANT_01", "LINE_A", "CNC-001", "spindle_speed_rpm")
    assert node_str == "Factory/PLANT_01/LINE_A/CNC-001/spindle_speed_rpm"


def test_opcua_variant_type_mapping():
    assert OPCUAMapper.get_variant_type(SignalType.FLOAT) == ua.VariantType.Double
    assert OPCUAMapper.get_variant_type(SignalType.INT) == ua.VariantType.Int64
    assert OPCUAMapper.get_variant_type(SignalType.BOOL) == ua.VariantType.Boolean
    assert OPCUAMapper.get_variant_type(SignalType.STRING) == ua.VariantType.String


def test_opcua_value_casting():
    assert OPCUAMapper.cast_to_variant_val(12.5, SignalType.FLOAT) == 12.5
    assert OPCUAMapper.cast_to_variant_val(42, SignalType.INT) == 42
    assert OPCUAMapper.cast_to_variant_val(True, SignalType.BOOL) is True
    assert OPCUAMapper.cast_to_variant_val("RUNNING", SignalType.ENUM) == "RUNNING"
