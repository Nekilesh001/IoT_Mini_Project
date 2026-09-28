"""
MQTT topic structure and JSON payload formatting rules.
"""

from typing import Any, Dict
from simulator.core.domain import MachineProfile


class MQTTMapper:
    """
    Handles deterministic MQTT topic generation and raw payload formatting.
    """

    MQTT_MACHINES = ["ROB-002", "PMP-001", "AGV-001"]

    @classmethod
    def get_telemetry_topic(cls, plant_id: str, line_id: str, machine_id: str) -> str:
        """Construct deterministic telemetry MQTT topic."""
        return f"factory/{plant_id}/{line_id}/{machine_id}/telemetry"

    @classmethod
    def get_status_topic(cls, plant_id: str, line_id: str, machine_id: str) -> str:
        """Construct status MQTT topic."""
        return f"factory/{plant_id}/{line_id}/{machine_id}/status"

    @classmethod
    def get_events_topic(cls, plant_id: str, line_id: str, machine_id: str) -> str:
        """Construct events MQTT topic."""
        return f"factory/{plant_id}/{line_id}/{machine_id}/events"

    @classmethod
    def encode_payload(cls, profile: MachineProfile, measurements: Dict[str, Any], sequence: int, operating_state: str, timestamp: str) -> Dict[str, Any]:
        """Encode machine telemetry into raw protocol-level JSON dictionary."""
        return {
            "machineId": profile.machine_id,
            "machineType": profile.machine_type.value,
            "timestamp": timestamp,
            "sequence": sequence,
            "operatingState": operating_state,
            "measurements": measurements
        }
