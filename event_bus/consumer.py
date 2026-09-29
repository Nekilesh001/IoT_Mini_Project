"""
Canonical Telemetry MQTT Consumer subscribing to event bus and persisting to repository.
"""

import json
import logging
from typing import Any, Callable, Dict, Optional

from edge.models import CanonicalTelemetry
from event_bus.topics import CanonicalTopicMapper
from storage.repository import TelemetryRepository
from storage.buffer import PersistentBuffer
from protocols.mqtt.broker import LocalMQTTBroker

logger = logging.getLogger(__name__)


class CanonicalTelemetryConsumer:
    """
    Subscribes to the canonical telemetry MQTT topic hierarchy,
    decodes canonical envelopes, and persists records into the database repository.
    """

    def __init__(
        self,
        repository: TelemetryRepository,
        host: str = "127.0.0.1",
        port: int = 1883,
        topic_filter: Optional[str] = None,
        buffer: Optional[PersistentBuffer] = None
    ):
        self._repository = repository
        self._host = host
        self._port = port
        self._topic_filter = topic_filter or CanonicalTopicMapper.get_wildcard_subscription()
        self._buffer = buffer
        self._broker = LocalMQTTBroker(host, port)
        self._is_connected = False
        self._consumed_count = 0
        self._persisted_count = 0
        self._duplicate_count = 0
        self._failed_count = 0

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    def start(self) -> None:
        """Start consumer subscription."""
        self._broker.subscribe(self._topic_filter, self._on_message)
        self._is_connected = True

    def stop(self) -> None:
        """Stop consumer."""
        self._broker.unsubscribe(self._topic_filter, self._on_message)
        self._is_connected = False

    def _on_message(self, topic: str, payload_str: Any, qos: int = 1) -> None:
        """Handle incoming canonical MQTT message."""
        self._consumed_count += 1
        try:
            if isinstance(payload_str, bytes):
                payload_str = payload_str.decode("utf-8")
            payload_dict = json.loads(payload_str)
            canonical = CanonicalTelemetry.from_dict(payload_dict)

            # Persist to database repository
            inserted = self._repository.insert(canonical)
            if inserted:
                self._persisted_count += 1
            else:
                self._duplicate_count += 1
        except Exception as e:
            logger.error(f"Failed to process/persist message from topic '{topic}': {e}")
            self._failed_count += 1
            if self._buffer:
                try:
                    payload_dict = json.loads(payload_str)
                    self._buffer.add_event(
                        event_id=payload_dict.get("eventId", "unknown"),
                        machine_id=payload_dict.get("machineId", "unknown"),
                        sequence=payload_dict.get("sequence", 0),
                        topic=topic,
                        payload_json=payload_str
                    )
                except Exception:
                    pass

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "is_connected": self._is_connected,
            "consumed_count": self._consumed_count,
            "persisted_count": self._persisted_count,
            "duplicate_count": self._duplicate_count,
            "failed_count": self._failed_count,
        }
