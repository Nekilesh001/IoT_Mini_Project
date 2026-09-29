"""
SQLAlchemy ORM models for Canonical Telemetry storage.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    BigInteger,
    Float,
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


class MLInferenceRecord(Base):
    """
    Relational table for Edge ML inference predictions and latency metadata.
    Stores real-time anomaly scores, predicted Remaining Useful Life (RUL), and model provenance.
    """
    __tablename__ = "ml_inferences"

    result_id = Column(String(64), primary_key=True, index=True)
    machine_id = Column(String(64), nullable=False, index=True)
    machine_type = Column(String(64), nullable=False)
    event_time = Column(DateTime(timezone=True), nullable=False, index=True)
    inference_time = Column(DateTime(timezone=True), nullable=False)

    anomaly_score = Column(Float, nullable=True)
    raw_anomaly_score = Column(Float, nullable=True)
    anomaly_label = Column(String(32), nullable=False, default="NORMAL", index=True)

    predicted_rul_seconds = Column(Float, nullable=True)
    predicted_rul_minutes = Column(Float, nullable=True)
    predicted_rul_hours = Column(Float, nullable=True)

    anomaly_model_name = Column(String(64), nullable=True)
    anomaly_model_version = Column(String(32), nullable=True)
    rul_model_name = Column(String(64), nullable=True)
    rul_model_version = Column(String(32), nullable=True)
    feature_manifest_version = Column(String(32), nullable=False, default="1.0.0")
    feature_count = Column(BigInteger, nullable=False, default=1019)
    runtime_backend = Column(String(32), nullable=False, default="SKLEARN")

    status = Column(String(32), nullable=False, default="READY", index=True)
    latency_ms = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    error_code = Column(String(64), nullable=True)
    error_message = Column(String(512), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_ml_machine_event_time", "machine_id", "event_time"),
        Index("ix_ml_machine_status", "machine_id", "status"),
        Index("ix_ml_event_time_desc", event_time.desc()),
    )

    def to_dict(self):
        return {
            "result_id": self.result_id,
            "machine_id": self.machine_id,
            "machine_type": self.machine_type,
            "event_time": self.event_time.isoformat() if self.event_time else None,
            "inference_time": self.inference_time.isoformat() if self.inference_time else None,
            "anomaly_score": self.anomaly_score,
            "raw_anomaly_score": self.raw_anomaly_score,
            "anomaly_label": self.anomaly_label,
            "predicted_rul_seconds": self.predicted_rul_seconds,
            "predicted_rul_minutes": self.predicted_rul_minutes,
            "predicted_rul_hours": self.predicted_rul_hours,
            "anomaly_model_name": self.anomaly_model_name,
            "anomaly_model_version": self.anomaly_model_version,
            "rul_model_name": self.rul_model_name,
            "rul_model_version": self.rul_model_version,
            "feature_manifest_version": self.feature_manifest_version,
            "feature_count": self.feature_count,
            "runtime_backend": self.runtime_backend,
            "status": self.status,
            "latency_ms": self.latency_ms or {},
            "error_code": self.error_code,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
