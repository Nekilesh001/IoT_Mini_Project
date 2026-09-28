"""
Sequence Tracker, Duplicate Detector, and Ordering Engine.
"""

from collections import deque
from typing import Any, Dict, Optional, Set, Tuple
from edge.models import IngestionStatus


class SequenceTracker:
    """
    Maintains per-machine sequence numbers and detects duplicate / out-of-order events.
    """

    def __init__(self, max_event_history: int = 1000):
        self._last_sequences: Dict[str, int] = {}
        self._seen_events: Set[str] = set()
        self._event_queue: deque = deque(maxlen=max_event_history)
        self._max_history: int = max_event_history

    def process_sequence(self, machine_id: str, sequence: int, event_id: Optional[str] = None) -> Tuple[IngestionStatus, Dict[str, Any]]:
        """
        Evaluate incoming sequence for machine_id.
        Returns (status, metrics_dict).
        """
        metrics = {
            "machine_id": machine_id,
            "received_sequence": sequence,
            "previous_sequence": self._last_sequences.get(machine_id),
            "gap_detected": False,
            "gap_size": 0,
        }

        # 1. Check event_id duplicate
        if event_id:
            if event_id in self._seen_events:
                return IngestionStatus.DUPLICATE, metrics
            self._seen_events.add(event_id)
            self._event_queue.append(event_id)
            if len(self._seen_events) > self._max_history:
                # Keep seen_events synchronized with deque
                self._seen_events = set(self._event_queue)

        # 2. First sequence for machine
        if machine_id not in self._last_sequences:
            self._last_sequences[machine_id] = sequence
            return IngestionStatus.ACCEPTED, metrics

        last_seq = self._last_sequences[machine_id]

        # 3. Exact duplicate sequence
        if sequence == last_seq:
            return IngestionStatus.DUPLICATE, metrics

        # 4. Out of order (older sequence)
        if sequence < last_seq:
            return IngestionStatus.OUT_OF_ORDER, metrics

        # 5. Increasing sequence (normal or gap)
        if sequence > last_seq:
            if sequence > last_seq + 1:
                metrics["gap_detected"] = True
                metrics["gap_size"] = sequence - (last_seq + 1)
            self._last_sequences[machine_id] = sequence
            return IngestionStatus.ACCEPTED, metrics

        return IngestionStatus.ACCEPTED, metrics

    def get_last_sequence(self, machine_id: str) -> Optional[int]:
        return self._last_sequences.get(machine_id)

    def reset(self) -> None:
        self._last_sequences.clear()
        self._seen_events.clear()
        self._event_queue.clear()
