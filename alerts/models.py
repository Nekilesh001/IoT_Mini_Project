"""
SQLAlchemy ORM models and domain schemas for Alert lifecycle management and persistence.
"""

from datetime import datetime, timezone
import uuid
from typing import Any, Dict, Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    JSON,
    Index,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from storage.database import Base
from alerts.rules import AlertSeverity, AlertStatus


class AlertRecord(Base):
    """
    Relational operational alert table.
    Stores active and historical alerts, triggering measurements, and acknowledgment status.
    """
    __tablename__ = "alerts"

    alert_id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    rule_id = Column(String(64), nullable=False, index=True)
    machine_id = Column(String(64), nullable=False, index=True)
    machine_type = Column(String(64), nullable=False)
    alert_code = Column(String(32), nullable=False)
    severity = Column(String(16), nullable=False, default=AlertSeverity.WARNING.value, index=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(16), nullable=False, default=AlertStatus.OPEN.value, index=True)

    triggered_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True
    )
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(String(64), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Dynamic heterogeneous physical measurements
    triggering_measurements = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    current_measurements = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    occurrence_count = Column(Integer, nullable=False, default=1)
    last_occurrence_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_alerts_machine_status", "machine_id", "status"),
        Index("idx_alerts_status_severity", "status", "severity"),
        Index("idx_alerts_triggered_at_desc", triggered_at.desc()),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "rule_id": self.rule_id,
            "machine_id": self.machine_id,
            "machine_type": self.machine_type,
            "alert_code": self.alert_code,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "acknowledged_by": self.acknowledged_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_notes": self.resolution_notes,
            "triggering_measurements": self.triggering_measurements,
            "current_measurements": self.current_measurements,
            "occurrence_count": self.occurrence_count,
            "last_occurrence_at": self.last_occurrence_at.isoformat() if self.last_occurrence_at else None,
        }
