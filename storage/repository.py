"""
Repository abstraction for persisting and querying canonical telemetry records.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, select

from edge.models import CanonicalTelemetry
from storage.models import TelemetryRecord

logger = logging.getLogger(__name__)


class TelemetryRepository:
    """
    Handles database operations for canonical telemetry records with idempotent conflict handling.
    """

    def __init__(self, session_factory):
        self._session_factory = session_factory

    @staticmethod
    def _to_record(canonical: CanonicalTelemetry) -> TelemetryRecord:
        # Parse ISO timestamps into datetime objects
        event_dt = datetime.fromisoformat(canonical.event_time)
        if event_dt.tzinfo is None:
            event_dt = event_dt.replace(tzinfo=timezone.utc)

        ingestion_dt = datetime.fromisoformat(canonical.ingestion_time)
        if ingestion_dt.tzinfo is None:
            ingestion_dt = ingestion_dt.replace(tzinfo=timezone.utc)

        return TelemetryRecord(
            event_id=canonical.event_id,
            schema_version=canonical.schema_version,
            event_type=canonical.event_type.value if hasattr(canonical.event_type, "value") else str(canonical.event_type),
            plant_id=canonical.plant_id,
            line_id=canonical.line_id,
            machine_id=canonical.machine_id,
            machine_type=canonical.machine_type,
            protocol=canonical.source.protocol,
            endpoint=canonical.source.endpoint,
            source_address=canonical.source.source_address,
            event_time=event_dt,
            ingestion_time=ingestion_dt,
            sequence=canonical.sequence,
            operating_state=canonical.state.operating,
            health_state=canonical.state.health,
            quality=canonical.quality.value if hasattr(canonical.quality, "value") else str(canonical.quality),
            measurements=canonical.measurements,
            derived=canonical.derived,
            ml=canonical.ml,
            received_at=datetime.now(timezone.utc)
        )

    def insert(self, canonical: CanonicalTelemetry) -> bool:
        """
        Idempotently insert a single canonical telemetry event.
        If event_id or (machine_id, sequence) already exists, returns False without raising error.
        """
        with self._session_factory() as session:
            try:
                # Check for duplicate event_id or machine_id + sequence
                existing = session.execute(
                    select(TelemetryRecord).where(
                        (TelemetryRecord.event_id == canonical.event_id) |
                        ((TelemetryRecord.machine_id == canonical.machine_id) & (TelemetryRecord.sequence == canonical.sequence))
                    )
                ).scalars().first()

                if existing:
                    logger.debug(f"Duplicate telemetry ignored: machine={canonical.machine_id}, seq={canonical.sequence}")
                    return False

                record = self._to_record(canonical)
                session.add(record)
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                logger.error(f"Error persisting telemetry record: {e}")
                raise

    def insert_many(self, telemetry_list: List[CanonicalTelemetry]) -> int:
        """
        Batch insert canonical telemetry records idempotently.
        Returns count of newly inserted records.
        """
        inserted_count = 0
        with self._session_factory() as session:
            try:
                for canonical in telemetry_list:
                    existing = session.execute(
                        select(TelemetryRecord).where(
                            (TelemetryRecord.event_id == canonical.event_id) |
                            ((TelemetryRecord.machine_id == canonical.machine_id) & (TelemetryRecord.sequence == canonical.sequence))
                        )
                    ).scalars().first()

                    if not existing:
                        session.add(self._to_record(canonical))
                        inserted_count += 1

                session.commit()
                return inserted_count
            except Exception as e:
                session.rollback()
                logger.error(f"Error in batch insert: {e}")
                raise

    def get_by_event_id(self, event_id: str) -> Optional[TelemetryRecord]:
        with self._session_factory() as session:
            return session.get(TelemetryRecord, event_id)

    def get_latest_by_machine(self, machine_id: str) -> Optional[TelemetryRecord]:
        with self._session_factory() as session:
            return session.execute(
                select(TelemetryRecord)
                .where(TelemetryRecord.machine_id == machine_id)
                .order_by(desc(TelemetryRecord.sequence))
            ).scalars().first()

    def get_machine_history(self, machine_id: str, limit: int = 100) -> List[TelemetryRecord]:
        with self._session_factory() as session:
            return list(session.execute(
                select(TelemetryRecord)
                .where(TelemetryRecord.machine_id == machine_id)
                .order_by(desc(TelemetryRecord.event_time))
                .limit(limit)
            ).scalars().all())

    def count_by_machine(self, machine_id: str) -> int:
        with self._session_factory() as session:
            return session.execute(
                select(func.count()).select_from(TelemetryRecord).where(TelemetryRecord.machine_id == machine_id)
            ).scalar_one()

    def query_time_range(self, machine_id: str, start_time: datetime, end_time: datetime) -> List[TelemetryRecord]:
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)

        with self._session_factory() as session:
            return list(session.execute(
                select(TelemetryRecord)
                .where(
                    (TelemetryRecord.machine_id == machine_id) &
                    (TelemetryRecord.event_time >= start_time) &
                    (TelemetryRecord.event_time <= end_time)
                )
                .order_by(TelemetryRecord.event_time.asc())
            ).scalars().all())
