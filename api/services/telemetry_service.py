"""
Service for Telemetry Queries and Time-Series History.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from storage.repository import TelemetryRepository
from simulator.core.domain import MachineProfile
from api.schemas.telemetry import (
    TelemetryRecordItem,
    TelemetryHistoryResponse,
)


class TelemetryService:
    def __init__(self, repository: TelemetryRepository, profiles: Dict[str, MachineProfile]):
        self._repo = repository
        self._profiles = profiles

    @staticmethod
    def _to_schema(rec) -> TelemetryRecordItem:
        return TelemetryRecordItem(
            event_id=rec.event_id,
            schema_version=rec.schema_version,
            event_type=rec.event_type,
            plant_id=rec.plant_id,
            line_id=rec.line_id,
            machine_id=rec.machine_id,
            machine_type=rec.machine_type,
            protocol=rec.protocol,
            endpoint=rec.endpoint,
            source_address=rec.source_address,
            event_time=rec.event_time.isoformat() if rec.event_time else "",
            ingestion_time=rec.ingestion_time.isoformat() if rec.ingestion_time else "",
            sequence=rec.sequence,
            operating_state=rec.operating_state,
            health_state=rec.health_state,
            quality=rec.quality,
            measurements=rec.measurements or {},
            derived=rec.derived or {},
            ml=rec.ml or {},
            received_at=rec.received_at.isoformat() if rec.received_at else None,
        )

    def get_latest_telemetry(self, machine_id: Optional[str] = None) -> List[TelemetryRecordItem]:
        if machine_id:
            rec = self._repo.get_latest_by_machine(machine_id)
            return [self._to_schema(rec)] if rec else []
        
        results = []
        for m_id in sorted(self._profiles.keys()):
            rec = self._repo.get_latest_by_machine(m_id)
            if rec:
                results.append(self._to_schema(rec))
        return results

    def get_machine_history(
        self,
        machine_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        signals: Optional[List[str]] = None
    ) -> TelemetryHistoryResponse:
        profile = self._profiles.get(machine_id)
        available_signals = [s.name for s in profile.signals] if profile else []

        if start_time and end_time:
            records = self._repo.query_time_range(machine_id, start_time, end_time)
            if limit and len(records) > limit:
                records = records[-limit:]
        else:
            records = self._repo.get_machine_history(machine_id, limit=limit)
            records = list(reversed(records))  # Chronological ascending order for charts

        schema_records = []
        for r in records:
            item = self._to_schema(r)
            if signals:
                item.measurements = {k: v for k, v in item.measurements.items() if k in signals}
            schema_records.append(item)

        return TelemetryHistoryResponse(
            machine_id=machine_id,
            total_records=len(schema_records),
            records=schema_records,
            available_signals=available_signals
        )
