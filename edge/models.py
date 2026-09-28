"""
Canonical Telemetry and Edge Ingestion domain models.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class EventType(str, Enum):
    TELEMETRY = "TELEMETRY"
    STATUS = "STATUS"
    FAULT = "FAULT"
    ALERT = "ALERT"
    COMMAND = "COMMAND"
    COMMAND_ACK = "COMMAND_ACK"
    CONFIG_UPDATE = "CONFIG_UPDATE"
    MAINTENANCE = "MAINTENANCE"


class QualityCode(str, Enum):
    GOOD = "GOOD"
    BAD = "BAD"
    STALE = "STALE"
    MISSING = "MISSING"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    ESTIMATED = "ESTIMATED"


class IngestionStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    DUPLICATE = "DUPLICATE"
    OUT_OF_ORDER = "OUT_OF_ORDER"
    INVALID = "INVALID"
    REJECTED = "REJECTED"


@dataclass
class CanonicalSource:
    protocol: str
    endpoint: str
    source_address: str = field(metadata={"name": "sourceAddress"})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "protocol": self.protocol,
            "endpoint": self.endpoint,
            "sourceAddress": self.source_address,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CanonicalSource":
        return cls(
            protocol=data.get("protocol", "UNKNOWN"),
            endpoint=data.get("endpoint", ""),
            source_address=data.get("sourceAddress", data.get("source_address", ""))
        )


@dataclass
class CanonicalState:
    operating: str = "RUNNING"
    health: str = "HEALTHY"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operating": self.operating,
            "health": self.health,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CanonicalState":
        return cls(
            operating=data.get("operating", "RUNNING"),
            health=data.get("health", "HEALTHY")
        )


@dataclass
class CanonicalTelemetry:
    schema_version: str
    event_id: str
    event_type: EventType
    plant_id: str
    line_id: str
    machine_id: str
    machine_type: str
    source: CanonicalSource
    event_time: str
    ingestion_time: str
    sequence: int
    state: CanonicalState
    quality: QualityCode
    measurements: Dict[str, Any]
    derived: Dict[str, Any] = field(default_factory=dict)
    ml: Dict[str, Any] = field(default_factory=dict)
    measurement_quality: Optional[Dict[str, QualityCode]] = None

    def to_dict(self) -> Dict[str, Any]:
        res = {
            "schemaVersion": self.schema_version,
            "eventId": self.event_id,
            "eventType": self.event_type.value,
            "plantId": self.plant_id,
            "lineId": self.line_id,
            "machineId": self.machine_id,
            "machineType": self.machine_type,
            "source": self.source.to_dict(),
            "eventTime": self.event_time,
            "ingestionTime": self.ingestion_time,
            "sequence": self.sequence,
            "state": self.state.to_dict(),
            "quality": self.quality.value,
            "measurements": self.measurements,
            "derived": self.derived,
            "ml": self.ml,
        }
        if self.measurement_quality:
            res["measurementQuality"] = {k: v.value for k, v in self.measurement_quality.items()}
        return res

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CanonicalTelemetry":
        return cls(
            schema_version=data.get("schemaVersion", "1.0.0"),
            event_id=data.get("eventId", f"evt_{uuid.uuid4()}"),
            event_type=EventType(data.get("eventType", "TELEMETRY")),
            plant_id=data.get("plantId", "PLANT_01"),
            line_id=data.get("lineId", "LINE_A"),
            machine_id=data.get("machineId", "UNKNOWN"),
            machine_type=data.get("machineType", "UNKNOWN"),
            source=CanonicalSource.from_dict(data.get("source", {})),
            event_time=data.get("eventTime", datetime.now(timezone.utc).isoformat()),
            ingestion_time=data.get("ingestionTime", datetime.now(timezone.utc).isoformat()),
            sequence=data.get("sequence", 0),
            state=CanonicalState.from_dict(data.get("state", {})),
            quality=QualityCode(data.get("quality", "GOOD")),
            measurements=data.get("measurements", {}),
            derived=data.get("derived", {}),
            ml=data.get("ml", {}),
            measurement_quality={k: QualityCode(v) for k, v in data.get("measurementQuality", {}).items()} if "measurementQuality" in data else None
        )


@dataclass
class IngestionResult:
    status: IngestionStatus
    canonical_telemetry: Optional[CanonicalTelemetry] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
