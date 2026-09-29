"""
Canonical Telemetry MQTT Publisher with automatic store-and-forward fallback.
"""

import json
import logging
from typing import Any, Dict, Optional

from edge.models import CanonicalTelemetry
from event_bus.topics import CanonicalTopicMapper
from storage.buffer import PersistentBuffer
from protocols.mqtt.broker import LocalMQTTBroker

logger = logging.getLogger(__name__)


class CanonicalTelemetryPublisher:
    """
    Publishes validated CanonicalTelemetry events to the MQTT event bus.
    If the broker is unavailable, falls back to the persistent store-and-forward buffer.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 1883,
        qos: int = 1,
        buffer: Optional[PersistentBuffer] = None
    ):
        self._host = host
        self._port = port
        self._qos = qos
        self._buffer = buffer
        self._broker = LocalMQTTBroker(host, port)
        self._is_connected = False
        self._published_count = 0
        self._failed_count = 0
        self._buffered_count = 0

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    def connect(self) -> bool:
        """Connect publisher to MQTT event bus broker."""
        self._broker.start()
        self._is_connected = True
        return True

    def disconnect(self) -> None:
        """Disconnect publisher."""
        self._is_connected = False
        self._broker.stop()

    def simulate_broker_outage(self) -> None:
        """Simulate broker failure for outage and recovery testing."""
        self._is_connected = False

    def restore_broker(self) -> None:
        """Restore broker connection after outage."""
        self._is_connected = True

    def publish(self, canonical: CanonicalTelemetry) -> bool:
        """
        Publish canonical telemetry event to MQTT topic.
        If publishing fails, stores event in persistent buffer.
        """
        topic = CanonicalTopicMapper.get_canonical_topic(
            plant_id=canonical.plant_id,
            line_id=canonical.line_id,
            machine_id=canonical.machine_id
        )
        payload_dict = canonical.to_dict()
        payload_json = json.dumps(payload_dict)

        if not self._is_connected:
            self._failed_count += 1
            if self._buffer:
                logger.warning(f"MQTT broker unavailable. Buffering canonical event {canonical.event_id}")
                self._buffer.add_event(
                    event_id=canonical.event_id,
                    machine_id=canonical.machine_id,
                    sequence=canonical.sequence,
                    topic=topic,
                    payload_json=payload_json
                )
                self._buffered_count += 1
            return False

        try:
            self._broker.publish(topic, payload_json, qos=self._qos)
            self._published_count += 1
            return True
        except Exception as e:
            logger.error(f"Failed to publish canonical telemetry event: {e}")
            self._failed_count += 1
            if self._buffer:
                self._buffer.add_event(
                    event_id=canonical.event_id,
                    machine_id=canonical.machine_id,
                    sequence=canonical.sequence,
                    topic=topic,
                    payload_json=payload_json
                )
                self._buffered_count += 1
            return False

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "is_connected": self._is_connected,
            "published_count": self._published_count,
            "failed_count": self._failed_count,
            "buffered_count": self._buffered_count,
        }
