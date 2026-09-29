"""
SQLAlchemy ORM models for Fault Scenario state management.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Float,
)
from storage.database import Base


class ScenarioStateRecord(Base):
    """
    Tracks persistent and active fault scenario states across API and background worker processes.
    """
    __tablename__ = "scenario_states"

    scenario_id = Column(String(64), primary_key=True)
    machine_id = Column(String(64), nullable=False, index=True)
    state = Column(String(32), nullable=False, default="INACTIVE")  # "INACTIVE", "ACTIVE", "STOPPED", "RESOLVED"
    elapsed_seconds = Column(Float, nullable=False, default=0.0)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self):
        return {
            "scenario_id": self.scenario_id,
            "machine_id": self.machine_id,
            "state": self.state,
            "elapsed_seconds": self.elapsed_seconds,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
