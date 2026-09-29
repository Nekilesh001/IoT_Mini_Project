"""
SQLAlchemy ORM models for Canonical Telemetry storage.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    BigInteger,
    DateTime,
    JSON,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from storage.database import Base


class TelemetryRecord(Base):
    """
    Relational time-series operational telemetry table.
    Heterogeneous sensor measurements, derived metrics, and ML metadata are stored in JSON/JSONB.
    """
    __tablename__ = "telemetry_records"

    event_id = Column(String(64), primary_key=True, index=True)
    schema_version = Column(String(16), nullable=False, default="1.0.0")
    event_type = Column(String(32), nullable=False, default="TELEMETRY")
    plant_id = Column(String(32), nullable=False, index=True)
    line_id = Column(String(32), nullable=False, index=True)
    machine_id = Column(String(64), nullable=False, index=True)
    machine_type = Column(String(64), nullable=False)
    protocol = Column(String(32), nullable=False)
    endpoint = Column(String(256), nullable=True)
    source_address = Column(String(256), nullable=False)
    event_time = Column(DateTime(timezone=True), nullable=False, index=True)
    ingestion_time = Column(DateTime(timezone=True), nullable=False)
    sequence = Column(BigInteger, nullable=False, index=True)
    operating_state = Column(String(32), nullable=False, default="RUNNING")
    health_state = Column(String(32), nullable=False, default="HEALTHY")
    quality = Column(String(32), nullable=False, default="GOOD")

    # Heterogeneous measurements, derived, and ML payloads
    measurements = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    derived = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    ml = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)

    received_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint("machine_id", "sequence", name="uq_telemetry_machine_sequence"),
        Index("ix_telemetry_machine_event_time", "machine_id", "event_time"),
        Index("ix_telemetry_plant_line_event_time", "plant_id", "line_id", "event_time"),
        Index("ix_telemetry_event_type_event_time", "event_type", "event_time"),
    )

    def to_dict(self):
        return {
            "schemaVersion": self.schema_version,
            "eventId": self.event_id,
            "eventType": self.event_type,
            "plantId": self.plant_id,
            "lineId": self.line_id,
            "machineId": self.machine_id,
            "machineType": self.machine_type,
            "source": {
                "protocol": self.protocol,
                "endpoint": self.endpoint or "",
                "sourceAddress": self.source_address,
            },
            "eventTime": self.event_time.isoformat() if self.event_time else None,
            "ingestionTime": self.ingestion_time.isoformat() if self.ingestion_time else None,
            "sequence": self.sequence,
            "state": {
                "operating": self.operating_state,
                "health": self.health_state,
            },
            "quality": self.quality,
            "measurements": self.measurements,
            "derived": self.derived or {},
            "ml": self.ml or {},
            "receivedAt": self.received_at.isoformat() if self.received_at else None,
        }
