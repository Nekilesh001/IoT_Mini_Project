"""
MQTT Client Adapter subscribing to telemetry topics and returning ProtocolReading objects.
"""

from datetime import datetime, timezone
import json
import logging
from typing import Dict, Optional

from simulator.core.domain import MachineProfile
from protocols.base import BaseProtocolAdapter
from protocols.models import ProtocolHealth, ProtocolReading, ProtocolType
from protocols.mqtt.mapping import MQTTMapper
from protocols.mqtt.broker import LocalMQTTBroker

logger = logging.getLogger(__name__)


class MQTTAdapter(BaseProtocolAdapter):
    """
    Subscriber adapter listening on MQTT topics and decoding JSON payloads into ProtocolReading objects.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 1883, profiles: Optional[Dict[str, MachineProfile]] = None):
        self._host: str = host
        self._port: int = port
        self._profiles: Dict[str, MachineProfile] = profiles or {}
        self._broker: LocalMQTTBroker = LocalMQTTBroker(host, port)
        self._is_connected: bool = False
        self._health: ProtocolHealth = ProtocolHealth.DISCONNECTED
        # machine_id -> latest payload_dict
        self._latest_messages: Dict[str, Dict[str, Any]] = {}

    @property
    def protocol_type(self) -> ProtocolType:
        return ProtocolType.MQTT

    def register_machine_profile(self, profile: MachineProfile) -> None:
        self._profiles[profile.machine_id] = profile

    def connect(self) -> bool:
        """Connect adapter and subscribe to factory MQTT topics."""
        if self._is_connected:
            return True

        topic_pattern = "factory/+/+/+/telemetry"
        self._broker.subscribe(topic_pattern, self._on_message)
        self._is_connected = True
        self._health = ProtocolHealth.CONNECTED
        return True

    def disconnect(self) -> None:
        """Disconnect adapter and unsubscribe."""
        topic_pattern = "factory/+/+/+/telemetry"
        self._broker.unsubscribe(topic_pattern, self._on_message)
        self._is_connected = False
        self._health = ProtocolHealth.DISCONNECTED

    def _on_message(self, topic: str, payload_bytes: bytes, qos: int) -> None:
        """Internal callback invoked when broker dispatches a message."""
        try:
            payload_str = payload_bytes.decode("utf-8")
            data = json.loads(payload_str)
            m_id = data.get("machineId")
            if m_id:
                data["_topic"] = topic
                data["_qos"] = qos
                self._latest_messages[m_id] = data
        except Exception as e:
            logger.error(f"MQTT adapter rejected malformed payload on topic '{topic}': {e}")
            self._health = ProtocolHealth.DEGRADED

    def read_telemetry(self, machine_id: str) -> Optional[ProtocolReading]:
        """
        Retrieve latest received MQTT message for machine_id and convert into a ProtocolReading object.
        """
        if not self._is_connected:
            self.connect()

        data = self._latest_messages.get(machine_id)
        if not data:
            return None

        profile = self._profiles.get(machine_id)
        m_type = profile.machine_type.value if profile else data.get("machineType", "UNKNOWN")
        topic = data.get("_topic", f"factory/PLANT_01/LINE_A/{machine_id}/telemetry")

        measurements = dict(data.get("measurements", {}))
        if "operatingState" in data:
            measurements["operating_state"] = data["operatingState"]

        return ProtocolReading(
            machine_id=machine_id,
            machine_type=m_type,
            protocol=ProtocolType.MQTT,
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            sequence=int(data.get("sequence", 0)),
            measurements=measurements,
            source_address=topic,
            raw_payload=data,
            metadata={"qos": data.get("_qos", 1), "topic": topic}
        )

    def get_health(self) -> ProtocolHealth:
        return self._health
