"""
PostgreSQL and relational telemetry database dataset collector.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import pandas as pd
from sqlalchemy.orm import sessionmaker

from ml.data.collectors import BaseTelemetryCollector
from storage.database import get_engine, get_session_factory
from storage.models import TelemetryRecord


class PostgresTelemetryCollector(BaseTelemetryCollector):
    """
    Collects observable telemetry records from the PostgreSQL / SQLite database.
    """

    def __init__(self, database_url: str):
        self._database_url = database_url
        self._engine = get_engine(database_url)
        self._session_factory = get_session_factory(self._engine)

    def collect(
        self,
        machine_ids: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        """Queries telemetry records from storage and extracts flattened measurements."""
        with self._session_factory() as session:
            query = session.query(TelemetryRecord)

            if machine_ids:
                query = query.filter(TelemetryRecord.machine_id.in_(machine_ids))
            if start_time:
                query = query.filter(TelemetryRecord.event_time >= start_time)
            if end_time:
                query = query.filter(TelemetryRecord.event_time <= end_time)

            query = query.order_by(TelemetryRecord.event_time.asc())

            if limit:
                query = query.limit(limit)

            records = query.all()

        if not records:
            return pd.DataFrame()

        rows: List[Dict[str, Any]] = []
        for r in records:
            row: Dict[str, Any] = {
                "event_id": r.event_id,
                "machine_id": r.machine_id,
                "machine_type": r.machine_type,
                "plant_id": r.plant_id,
                "line_id": r.line_id,
                "protocol": r.protocol,
                "event_time": r.event_time.isoformat() if r.event_time else None,
                "sequence": r.sequence,
                "operating_state": r.operating_state,
                "health_state": r.health_state,
                "quality": r.quality,
            }
            # Flatten measurements and derived
            if isinstance(r.measurements, dict):
                row.update(r.measurements)
            if isinstance(r.derived, dict):
                row.update({f"derived_{k}": v for k, v in r.derived.items()})

            rows.append(row)

        df = pd.DataFrame(rows)
        if "event_time" in df.columns:
            df["event_time"] = pd.to_datetime(df["event_time"])
            df = df.sort_values(["machine_id", "event_time"]).reset_index(drop=True)
        return df
