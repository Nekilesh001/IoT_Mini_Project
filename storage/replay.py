"""
Replay worker service with exponential backoff for replaying buffered telemetry.
"""

import json
import logging
import threading
import time
from typing import Any, Dict, List, Optional

from edge.models import CanonicalTelemetry
from storage.buffer import PersistentBuffer, BufferedEvent
from storage.repository import TelemetryRepository

logger = logging.getLogger(__name__)


class ReplayWorker:
    """
    Background worker that continuously retries buffered events with exponential backoff
    until successful delivery or maximum retry limits are reached.
    """

    def __init__(
        self,
        buffer: PersistentBuffer,
        repository: Optional[TelemetryRepository] = None,
        publisher: Optional[Any] = None,
        initial_delay_sec: float = 1.0,
        max_delay_sec: float = 30.0,
        max_retries: int = 10,
        batch_size: int = 50,
        poll_interval_sec: float = 0.5
    ):
        self._buffer = buffer
        self._repository = repository
        self._publisher = publisher
        self._initial_delay = initial_delay_sec
        self._max_delay = max_delay_sec
        self._max_retries = max_retries
        self._batch_size = batch_size
        self._poll_interval = poll_interval_sec
        self._is_running = False
        self._thread: Optional[threading.Thread] = None
        self._replayed_count = 0
        self._failed_replay_count = 0

    def start(self) -> None:
        if self._is_running:
            return
        self._is_running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._is_running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _run_loop(self) -> None:
        while self._is_running:
            try:
                self.replay_batch()
            except Exception as e:
                logger.error(f"Error in replay worker loop: {e}")
            time.sleep(self._poll_interval)

    def replay_batch(self) -> int:
        """
        Process a single batch of pending buffered events.
        Returns count of successfully replayed events.
        """
        events = self._buffer.get_pending_events(batch_size=self._batch_size)
        if not events:
            return 0

        self._buffer.mark_in_flight([e.event_id for e in events])
        delivered_ids = []

        for event in events:
            success = False
            error_msg = ""
            try:
                payload_dict = event.get_payload_dict()
                canonical = CanonicalTelemetry.from_dict(payload_dict)

                # 1. Try replaying to MQTT publisher if available and connected
                if self._publisher and getattr(self._publisher, "is_connected", False):
                    success = self._publisher.publish(canonical)
                # 2. Or replay directly to repository if available
                elif self._repository:
                    self._repository.insert(canonical)
                    success = True
                else:
                    error_msg = "No active publisher or repository available for replay"
            except Exception as e:
                error_msg = str(e)
                success = False

            if success:
                delivered_ids.append(event.event_id)
                self._replayed_count += 1
            else:
                self._failed_replay_count += 1
                # Calculate exponential backoff delay
                delay = min(self._max_delay, self._initial_delay * (2 ** event.retry_count))
                self._buffer.mark_retry_failed(
                    event_id=event.event_id,
                    error=error_msg or "Replay delivery failed",
                    retry_delay_sec=delay,
                    max_retries=self._max_retries
                )

        if delivered_ids:
            self._buffer.mark_delivered(delivered_ids, delete_on_success=True)

        return len(delivered_ids)

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "is_running": self._is_running,
            "replayed_count": self._replayed_count,
            "failed_replay_count": self._failed_replay_count,
            "pending_buffer_count": self._buffer.count_by_status("PENDING"),
            "failed_buffer_count": self._buffer.count_by_status("FAILED"),
        }
