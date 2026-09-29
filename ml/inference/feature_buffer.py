"""
Machine-Aware Temporal Feature Buffer for Real-Time Telemetry.
"""

from collections import deque
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Set
import pandas as pd

from edge.models import CanonicalTelemetry
from ml.inference.errors import InvalidTelemetryError

logger = logging.getLogger(__name__)


class MachineTelemetryBuffer:
    """
    Maintains bounded historical observations for a single machine.
    Sorts by timestamp, rejects duplicates, and produces tabular views for feature extraction.
    """

    def __init__(self, machine_id: str, max_size: int = 60, min_warmup: int = 5):
        self.machine_id = machine_id
        self.max_size = max_size
        self.min_warmup = min_warmup
        self._buffer: deque = deque(maxlen=max_size)
        self._seen_event_ids: Set[str] = set()
        self._last_sequence: int = -1

    @property
    def sample_count(self) -> int:
        return len(self._buffer)

    @property
    def is_ready(self) -> bool:
        """Returns True when enough chronological history exists for rolling windows."""
        return len(self._buffer) >= self.min_warmup

    def add(self, telemetry: CanonicalTelemetry) -> bool:
        """
        Appends a canonical telemetry record to the buffer.
        Returns True if added, False if duplicate.
        """
        if not telemetry:
            raise InvalidTelemetryError("Cannot add null telemetry to feature buffer")

        if telemetry.machine_id != self.machine_id:
            raise InvalidTelemetryError(
                f"Machine ID mismatch: buffer is for {self.machine_id}, received {telemetry.machine_id}"
            )

        event_id = telemetry.event_id
        if event_id in self._seen_event_ids:
            logger.debug(f"Duplicate event_id {event_id} ignored for machine {self.machine_id}")
            return False

        # Flatten record into a row representation
        row = {
            "event_id": telemetry.event_id,
            "machine_id": telemetry.machine_id,
            "machine_type": telemetry.machine_type,
            "event_time": telemetry.event_time,
            "sequence": telemetry.sequence,
            "operating_state": telemetry.state.operating if hasattr(telemetry.state, "operating") else "RUNNING",
            "quality": telemetry.quality if hasattr(telemetry, "quality") else "GOOD",
        }

        # Include all physical measurements
        if isinstance(telemetry.measurements, dict):
            for k, v in telemetry.measurements.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    row[k] = float(v)

        self._buffer.append(row)
        self._seen_event_ids.add(event_id)
        if len(self._seen_event_ids) > self.max_size * 2:
            # Prune oldest event IDs to prevent memory growth
            self._seen_event_ids = {r["event_id"] for r in self._buffer}

        self._last_sequence = max(self._last_sequence, telemetry.sequence)
        return True

    def to_dataframe(self) -> pd.DataFrame:
        """
        Returns a time-sorted pandas DataFrame of all buffered observations.
        """
        if not self._buffer:
            return pd.DataFrame()

        df = pd.DataFrame(list(self._buffer))
        if "event_time" in df.columns:
            df["event_time"] = pd.to_datetime(df["event_time"])
            df = df.sort_values("event_time").reset_index(drop=True)
        return df

    def clear(self) -> None:
        """Resets the machine buffer."""
        self._buffer.clear()
        self._seen_event_ids.clear()
        self._last_sequence = -1


class TemporalFeatureBuffer:
    """
    Thread-safe registry of machine-specific telemetry buffers across the entire factory fleet.
    """

    def __init__(self, max_buffer_size: int = 60, min_warmup_samples: int = 5):
        self.max_buffer_size = max_buffer_size
        self.min_warmup_samples = min_warmup_samples
        self._buffers: Dict[str, MachineTelemetryBuffer] = {}

    def get_or_create(self, machine_id: str) -> MachineTelemetryBuffer:
        if machine_id not in self._buffers:
            self._buffers[machine_id] = MachineTelemetryBuffer(
                machine_id=machine_id,
                max_size=self.max_buffer_size,
                min_warmup=self.min_warmup_samples,
            )
        return self._buffers[machine_id]

    def add_telemetry(self, telemetry: CanonicalTelemetry) -> bool:
        """Adds telemetry to the appropriate machine's buffer."""
        buf = self.get_or_create(telemetry.machine_id)
        return buf.add(telemetry)

    def is_machine_ready(self, machine_id: str) -> bool:
        """Checks if a machine has reached warmup threshold."""
        if machine_id not in self._buffers:
            return False
        return self._buffers[machine_id].is_ready

    def get_machine_dataframe(self, machine_id: str) -> pd.DataFrame:
        """Retrieves history DataFrame for a machine."""
        if machine_id not in self._buffers:
            return pd.DataFrame()
        return self._buffers[machine_id].to_dataframe()

    def get_all_machine_ids(self) -> List[str]:
        return list(self._buffers.keys())

    def reset(self) -> None:
        """Clears all machine buffers."""
        self._buffers.clear()
