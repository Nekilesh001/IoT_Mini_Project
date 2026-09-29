"""
Realtime Server-Sent Events (SSE) streaming service for live telemetry updates.
"""

import asyncio
import json
import logging
from typing import AsyncGenerator, Dict
from storage.repository import TelemetryRepository
from simulator.core.domain import MachineProfile

logger = logging.getLogger(__name__)


class RealtimeService:
    def __init__(self, repository: TelemetryRepository, profiles: Dict[str, MachineProfile], interval_seconds: float = 1.0):
        self._repo = repository
        self._profiles = profiles
        self._interval = interval_seconds

    async def event_generator(self) -> AsyncGenerator[str, None]:
        """
        Yields SSE telemetry events as new database records arrive.
        """
        last_sequences: Dict[str, int] = {}

        # Initial emission of current latest snapshots upon connection
        for m_id, profile in sorted(self._profiles.items()):
            latest = self._repo.get_latest_by_machine(m_id)
            if latest:
                last_sequences[m_id] = latest.sequence
                event_data = {
                    "machine_id": m_id,
                    "machine_type": profile.machine_type.value if hasattr(profile.machine_type, "value") else str(profile.machine_type),
                    "protocol": profile.protocol_metadata.value if hasattr(profile.protocol_metadata, "value") else str(profile.protocol_metadata),
                    "event_id": latest.event_id,
                    "sequence": latest.sequence,
                    "event_time": latest.event_time.isoformat() if latest.event_time else "",
                    "operating_state": latest.operating_state,
                    "health_state": latest.health_state,
                    "quality": latest.quality,
                    "measurements": latest.measurements or {},
                    "derived": latest.derived or {},
                }
                yield f"data: {json.dumps(event_data)}\n\n"

        while True:
            new_events_found = False
            for m_id, profile in sorted(self._profiles.items()):
                latest = self._repo.get_latest_by_machine(m_id)
                if latest:
                    last_seq = last_sequences.get(m_id, 0)
                    if latest.sequence > last_seq:
                        last_sequences[m_id] = latest.sequence
                        new_events_found = True

                        event_data = {
                            "machine_id": m_id,
                            "machine_type": profile.machine_type.value if hasattr(profile.machine_type, "value") else str(profile.machine_type),
                            "protocol": profile.protocol_metadata.value if hasattr(profile.protocol_metadata, "value") else str(profile.protocol_metadata),
                            "event_id": latest.event_id,
                            "sequence": latest.sequence,
                            "event_time": latest.event_time.isoformat() if latest.event_time else "",
                            "operating_state": latest.operating_state,
                            "health_state": latest.health_state,
                            "quality": latest.quality,
                            "measurements": latest.measurements or {},
                            "derived": latest.derived or {},
                        }
                        yield f"data: {json.dumps(event_data)}\n\n"

            # Heartbeat comment if no new events to prevent timeout
            if not new_events_found:
                yield ": heartbeat\n\n"

            await asyncio.sleep(self._interval)
