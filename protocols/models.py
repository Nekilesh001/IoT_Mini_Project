"""
Protocol data models and health state representations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional
from datetime import datetime, timezone


class ProtocolType(str, Enum):
    MODBUS_TCP = "MODBUS_TCP"
    OPC_UA = "OPC_UA"
    MQTT = "MQTT"


class ProtocolHealth(str, Enum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"


@dataclass
class ProtocolReading:
    """
    Adapter-level reading object produced when reading/receiving telemetry
    from a protocol server or broker.
    """
    machine_id: str
    machine_type: str
    protocol: ProtocolType
    timestamp: str
    sequence: int
    measurements: Dict[str, Any]
    source_address: str
    raw_payload: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "machineId": self.machine_id,
            "machineType": self.machine_type,
            "protocol": self.protocol.value,
            "timestamp": self.timestamp,
            "sequence": self.sequence,
            "measurements": self.measurements,
            "sourceAddress": self.source_address,
            "metadata": self.metadata
        }
