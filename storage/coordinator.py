"""
Service coordinator orchestrating local event bus, database repository, buffer, and replay worker.
"""

import logging
from typing import Any, Dict, Optional

from edge.models import CanonicalTelemetry
from storage.config import StorageConfig, MQTTConfig, BufferConfig
from storage.database import get_engine, get_session_factory, init_db
from storage.models import Base
from storage.repository import TelemetryRepository
from storage.buffer import PersistentBuffer
from storage.replay import ReplayWorker
from event_bus.publisher import CanonicalTelemetryPublisher
from event_bus.consumer import CanonicalTelemetryConsumer

logger = logging.getLogger(__name__)


class Phase4ServiceCoordinator:
    """
    Coordinates all Phase 4 local operational services:
    Database repository, MQTT publisher, consumer subscriber, persistent buffer, and replay worker.
    """

    def __init__(
        self,
        db_url: Optional[str] = None,
        buffer_path: Optional[str] = None,
        mqtt_host: str = "127.0.0.1",
        mqtt_port: int = 1883
    ):
        self._db_url = db_url or StorageConfig().database_url
        self._buffer_path = buffer_path or BufferConfig().db_path
        self._mqtt_host = mqtt_host
        self._mqtt_port = mqtt_port

        # Initialize Database
        self._engine = get_engine(self._db_url)
        self._session_factory = get_session_factory(self._engine)
        init_db(self._engine)
        self._repository = TelemetryRepository(self._session_factory)

        # Initialize Buffer
        self._buffer = PersistentBuffer(self._buffer_path)

        # Initialize Publisher & Consumer
        self._publisher = CanonicalTelemetryPublisher(
            host=self._mqtt_host,
            port=self._mqtt_port,
            buffer=self._buffer
        )
        self._consumer = CanonicalTelemetryConsumer(
            repository=self._repository,
            host=self._mqtt_host,
            port=self._mqtt_port,
            buffer=self._buffer
        )

        # Initialize Replay Worker
        self._replay_worker = ReplayWorker(
            buffer=self._buffer,
            repository=self._repository,
            publisher=self._publisher
        )

        self._is_running = False

    @property
    def repository(self) -> TelemetryRepository:
        return self._repository

    @property
    def buffer(self) -> PersistentBuffer:
        return self._buffer

    @property
    def publisher(self) -> CanonicalTelemetryPublisher:
        return self._publisher

    @property
    def consumer(self) -> CanonicalTelemetryConsumer:
        return self._consumer

    @property
    def replay_worker(self) -> ReplayWorker:
        return self._replay_worker

    def start(self) -> None:
        """Start publisher, consumer, and replay worker."""
        if self._is_running:
            return
        self._publisher.connect()
        self._consumer.start()
        self._replay_worker.start()
        self._is_running = True
        logger.info("Phase 4 local operational services started.")

    def stop(self) -> None:
        """Stop all services cleanly."""
        if not self._is_running:
            return
        self._replay_worker.stop()
        self._consumer.stop()
        self._publisher.disconnect()
        self._engine.dispose()
        self._is_running = False
        logger.info("Phase 4 local operational services stopped.")

    def process_canonical_telemetry(self, canonical: CanonicalTelemetry) -> bool:
        """
        Process a CanonicalTelemetry event:
        1. Publish to MQTT event bus.
        2. If publish fails, it is automatically written to persistent buffer.
        """
        return self._publisher.publish(canonical)

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "publisher": self._publisher.get_metrics(),
            "consumer": self._consumer.get_metrics(),
            "replay": self._replay_worker.get_metrics(),
            "buffer_pending": self._buffer.count_by_status("PENDING"),
        }
