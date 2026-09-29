"""
Realtime Server-Sent Events (SSE) streaming service for live telemetry and operational alerts.
"""

import asyncio
from datetime import datetime
import json
import logging
from typing import AsyncGenerator, Dict, Optional
from storage.repository import TelemetryRepository
from simulator.core.domain import MachineProfile
from alerts.repository import AlertRepository

logger = logging.getLogger(__name__)


class RealtimeService:
    def __init__(
        self,
        repository: TelemetryRepository,
        profiles: Dict[str, MachineProfile],
        alert_repository: Optional[AlertRepository] = None,
        interval_seconds: float = 1.0
    ):
        self._repo = repository
        self._profiles = profiles
        self._alert_repo = alert_repository
        self._interval = interval_seconds

    async def event_generator(self) -> AsyncGenerator[str, None]:
        """
        Yields SSE telemetry events as new database records arrive.
        """
        last_sequences: Dict[str, int] = {}
        last_alert_check: Optional[datetime] = None

        # Initial emission of current latest snapshots upon connection
        for m_id, profile in sorted(self._profiles.items()):
            latest = self._repo.get_latest_by_machine(m_id)
            if latest:
                last_sequences[m_id] = latest.sequence
                event_data = {
                    "event_type": "TELEMETRY",
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
                yield f"event: telemetry\ndata: {json.dumps(event_data)}\n\n"

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
                            "event_type": "TELEMETRY",
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
                        # Send both raw data and named event for maximum client compatibility
                        yield f"event: telemetry\ndata: {json.dumps(event_data)}\n\n"

            # Check for active alerts if alert repository is available
            if self._alert_repo:
                try:
                    active_alerts = self._alert_repo.list_active_alerts(limit=50)
                    if active_alerts:
                        alert_summary = self._alert_repo.get_summary()
                        alert_payload = {
                            "event_type": "ALERT_UPDATE",
                            "summary": alert_summary,
                            "active_alerts": [a.to_dict() for a in active_alerts[:10]],
                        }
                        yield f"event: alert\ndata: {json.dumps(alert_payload)}\n\n"
                except Exception as e:
                    logger.debug(f"Alert stream polling notice: {e}")

            # Heartbeat comment if no new events to prevent timeout
            if not new_events_found:
                yield ": heartbeat\n\n"

            await asyncio.sleep(self._interval)

    async def alert_event_generator(self) -> AsyncGenerator[str, None]:
        """Dedicated SSE stream for alert events."""
        if not self._alert_repo:
            return

        while True:
            try:
                active_alerts = self._alert_repo.list_active_alerts(limit=100)
                summary = self._alert_repo.get_summary()
                payload = {
                    "event_type": "ALERT_UPDATE",
                    "summary": summary,
                    "active_alerts": [a.to_dict() for a in active_alerts],
                }
                yield f"data: {json.dumps(payload)}\n\n"
            except Exception as e:
                logger.error(f"Alert SSE generator error: {e}")
            await asyncio.sleep(self._interval)
