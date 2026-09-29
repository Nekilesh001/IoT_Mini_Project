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


class MLInferenceRepository:
    """
    Handles database operations and queries for Edge ML Inference records.
    """

    def __init__(self, session_factory):
        self._session_factory = session_factory

    def insert(self, result: Any) -> bool:
        """
        Idempotently inserts an ML inference result into the database.
        Accepts MLInferenceResult or dict.
        """
        from storage.models import MLInferenceRecord

        res_dict = result.to_dict() if hasattr(result, "to_dict") else dict(result)
        res_id = res_dict.get("result_id")
        m_id = res_dict.get("machine_id")

        ev_time = res_dict.get("event_time")
        if isinstance(ev_time, str):
            ev_time = datetime.fromisoformat(ev_time)
        if ev_time and ev_time.tzinfo is None:
            ev_time = ev_time.replace(tzinfo=timezone.utc)

        inf_time = res_dict.get("inference_time")
        if isinstance(inf_time, str):
            inf_time = datetime.fromisoformat(inf_time)
        if inf_time and inf_time.tzinfo is None:
            inf_time = inf_time.replace(tzinfo=timezone.utc)

        with self._session_factory() as session:
            try:
                # Check for existing result_id or same machine + event_time
                existing = session.execute(
                    select(MLInferenceRecord).where(
                        (MLInferenceRecord.result_id == res_id) |
                        ((MLInferenceRecord.machine_id == m_id) & (MLInferenceRecord.event_time == ev_time))
                    )
                ).scalars().first()

                if existing:
                    return False

                rec = MLInferenceRecord(
                    result_id=res_id,
                    machine_id=m_id,
                    machine_type=res_dict.get("machine_type", "UNKNOWN"),
                    event_time=ev_time,
                    inference_time=inf_time or datetime.now(timezone.utc),
                    anomaly_score=res_dict.get("anomaly_score"),
                    raw_anomaly_score=res_dict.get("raw_anomaly_score"),
                    anomaly_label=res_dict.get("anomaly_label", "NORMAL"),
                    predicted_rul_seconds=res_dict.get("predicted_rul_seconds"),
                    predicted_rul_minutes=res_dict.get("predicted_rul_minutes"),
                    predicted_rul_hours=res_dict.get("predicted_rul_hours"),
                    anomaly_model_name=res_dict.get("anomaly_model_name"),
                    anomaly_model_version=res_dict.get("anomaly_model_version"),
                    rul_model_name=res_dict.get("rul_model_name"),
                    rul_model_version=res_dict.get("rul_model_version"),
                    feature_manifest_version=res_dict.get("feature_manifest_version", "1.0.0"),
                    feature_count=res_dict.get("feature_count", 1019),
                    runtime_backend=res_dict.get("runtime_backend", "SKLEARN"),
                    status=res_dict.get("status", "READY"),
                    latency_ms=res_dict.get("latency_ms", {}),
                    error_code=res_dict.get("error_code"),
                    error_message=res_dict.get("error_message"),
                    created_at=datetime.now(timezone.utc),
                )
                session.add(rec)
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                logger.error(f"Error persisting ML inference: {e}")
                raise

    def get_latest_by_machine(self, machine_id: str) -> Optional[Any]:
        from storage.models import MLInferenceRecord
        with self._session_factory() as session:
            return session.execute(
                select(MLInferenceRecord)
                .where(MLInferenceRecord.machine_id == machine_id)
                .order_by(desc(MLInferenceRecord.event_time))
            ).scalars().first()

    def get_history(self, machine_id: str, limit: int = 100) -> List[Any]:
        from storage.models import MLInferenceRecord
        with self._session_factory() as session:
            return list(session.execute(
                select(MLInferenceRecord)
                .where(MLInferenceRecord.machine_id == machine_id)
                .order_by(desc(MLInferenceRecord.event_time))
                .limit(limit)
            ).scalars().all())

    def list_recent(self, limit: int = 100) -> List[Any]:
        from storage.models import MLInferenceRecord
        with self._session_factory() as session:
            return list(session.execute(
                select(MLInferenceRecord)
                .order_by(desc(MLInferenceRecord.event_time))
                .limit(limit)
            ).scalars().all())

    def get_fleet_summary(self) -> Dict[str, Any]:
        from storage.models import MLInferenceRecord
        with self._session_factory() as session:
            total_inferences = session.execute(select(func.count()).select_from(MLInferenceRecord)).scalar_one()
            anomalous_count = session.execute(
                select(func.count()).select_from(MLInferenceRecord).where(MLInferenceRecord.anomaly_label == "ANOMALOUS")
            ).scalar_one()

            # Find latest prediction per machine
            subquery = select(
                MLInferenceRecord.machine_id,
                func.max(MLInferenceRecord.event_time).label("max_time")
            ).group_by(MLInferenceRecord.machine_id).subquery()

            latest_records = session.execute(
                select(MLInferenceRecord).join(
                    subquery,
                    (MLInferenceRecord.machine_id == subquery.c.machine_id) &
                    (MLInferenceRecord.event_time == subquery.c.max_time)
                )
            ).scalars().all()

            active_anomalous_machines = [r.machine_id for r in latest_records if r.anomaly_label == "ANOMALOUS"]
            low_rul_machines = [
                r.machine_id for r in latest_records
                if r.predicted_rul_seconds is not None and r.predicted_rul_seconds < 1800.0
            ]

            return {
                "total_inferences": total_inferences,
                "anomalous_inferences_total": anomalous_count,
                "monitored_machines_count": len(latest_records),
                "active_anomalous_machines": active_anomalous_machines,
                "low_rul_machines": low_rul_machines,
            }
