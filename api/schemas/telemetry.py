"""
Telemetry Schemas for Canonical records, History and Realtime Streaming.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TelemetryRecordItem(BaseModel):
    event_id: str
    schema_version: str = "1.0.0"
    event_type: str = "TELEMETRY"
    plant_id: str
    line_id: str
    machine_id: str
    machine_type: str
    protocol: str
    endpoint: Optional[str] = None
    source_address: str
    event_time: str
    ingestion_time: str
    sequence: int
    operating_state: str
    health_state: str
    quality: str
    measurements: Dict[str, Any]
    derived: Optional[Dict[str, Any]] = None
    ml: Optional[Dict[str, Any]] = None
    received_at: Optional[str] = None


class TelemetryHistoryResponse(BaseModel):
    machine_id: str
    total_records: int
    records: List[TelemetryRecordItem]
    available_signals: List[str]


class RealtimeTelemetryEvent(BaseModel):
    machine_id: str
    machine_type: str
    protocol: str
    event_id: str
    sequence: int
    event_time: str
    operating_state: str
    health_state: str
    quality: str
    measurements: Dict[str, Any]
    derived: Optional[Dict[str, Any]] = None
