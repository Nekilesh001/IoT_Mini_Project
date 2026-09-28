"""
MQTT Publisher Manager publishing machine telemetry over MQTT topic hierarchy.
"""

import json
import logging
from typing import Dict, Optional

from simulator.core.domain import TelemetrySnapshot, MachineProfile
from protocols.base import BaseProtocolServer
from protocols.models import ProtocolHealth, ProtocolType
from protocols.mqtt.mapping import MQTTMapper
from protocols.mqtt.broker import LocalMQTTBroker

logger = logging.getLogger(__name__)


class MQTTPublisherManager(BaseProtocolServer):
    """
    Manages MQTT publishers for MQTT-assigned machines (ROB-002, PMP-001, AGV-001).
    Publishes to factory/{plant_id}/{line_id}/{machine_id}/telemetry with QoS 1.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 1883, profiles: Optional[Dict[str, MachineProfile]] = None, qos: int = 1):
        self._host: str = host
        self._port: int = port
        self._profiles: Dict[str, MachineProfile] = profiles or {}
        self._qos: int = qos
        self._broker: LocalMQTTBroker = LocalMQTTBroker(host, port)
        self._is_running: bool = False
        self._health: ProtocolHealth = ProtocolHealth.DISCONNECTED

    @property
    def protocol_type(self) -> ProtocolType:
        return ProtocolType.MQTT

    @property
    def is_running(self) -> bool:
        return self._is_running

    def register_machine_profile(self, profile: MachineProfile) -> None:
        self._profiles[profile.machine_id] = profile

    def start(self) -> None:
        """Start MQTT publisher service and local broker."""
        self._broker.start()
        self._is_running = True
        self._health = ProtocolHealth.CONNECTED

    def stop(self) -> None:
        """Stop MQTT publisher service cleanly."""
        self._is_running = False
        self._health = ProtocolHealth.DISCONNECTED
        self._broker.stop()

    def update_from_telemetry(self, snapshot: TelemetrySnapshot) -> None:
        """
        Encode snapshot measurements into raw protocol JSON payload and publish to MQTT topic.
        """
        if not self._is_running:
            return

        machine_id = snapshot.machine_id
        if machine_id not in MQTTMapper.MQTT_MACHINES:
            return

        profile = self._profiles.get(machine_id)
        if not profile:
            return

        topic = MQTTMapper.get_telemetry_topic(profile.plant_id, profile.line_id, machine_id)
        payload_dict = MQTTMapper.encode_payload(
            profile=profile,
            measurements=snapshot.public_measurements,
            sequence=snapshot.sequence,
            operating_state=snapshot.operating_state,
            timestamp=snapshot.timestamp
        )

        payload_bytes = json.dumps(payload_dict).encode("utf-8")
        self._broker.publish(topic, payload_bytes, qos=self._qos)

    def get_health(self) -> ProtocolHealth:
        return self._health
