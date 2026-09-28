"""
OPC UA node namespace mapping and variant type conversion rules.
"""

from typing import Any, Dict
from asyncua import ua
from simulator.core.domain import MachineProfile, SignalType


class OPCUAMapper:
    """
    Handles deterministic mapping between Python machine signals and OPC UA Nodes.
    """

    NAMESPACE_URI: str = "http://smartfactory.org/opcua"

    OPCUA_MACHINES = ["CNC-001", "ROB-001", "IMM-001", "VIS-001"]

    @classmethod
    def get_node_id_string(cls, plant_id: str, line_id: str, machine_id: str, signal_name: str) -> str:
        """Construct deterministic node ID string."""
        return f"Factory/{plant_id}/{line_id}/{machine_id}/{signal_name}"

    @classmethod
    def get_variant_type(cls, signal_type: SignalType) -> ua.VariantType:
        """Map Python signal type enum to OPC UA variant type."""
        if signal_type == SignalType.FLOAT:
            return ua.VariantType.Double
        elif signal_type == SignalType.INT:
            return ua.VariantType.Int64
        elif signal_type == SignalType.BOOL:
            return ua.VariantType.Boolean
        else: # STRING / ENUM
            return ua.VariantType.String

    @classmethod
    def cast_to_variant_val(cls, value: Any, signal_type: SignalType) -> Any:
        """Cast value to native Python type suitable for asyncua Variant."""
        if value is None:
            return 0.0 if signal_type == SignalType.FLOAT else (0 if signal_type == SignalType.INT else "")

        if signal_type == SignalType.FLOAT:
            return float(value)
        elif signal_type == SignalType.INT:
            return int(value)
        elif signal_type == SignalType.BOOL:
            return bool(value)
        else:
            return str(value)
