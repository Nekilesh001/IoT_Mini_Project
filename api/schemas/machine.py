"""
Machine Schemas for API responses.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SignalMetadataItem(BaseModel):
    name: str
    signal_type: str
    unit: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    nominal_value: Optional[Any] = None
    description: str


class MachineOverviewItem(BaseModel):
    machine_id: str
    machine_type: str
    protocol: str
    plant_id: str
    line_id: str
    operating_state: str
    health_state: str
    quality: str
    sequence: int
    latest_event_time: Optional[str] = None
    key_measurements: Dict[str, Any] = Field(default_factory=dict)


class MachineDetailResponse(BaseModel):
    machine_id: str
    machine_type: str
    protocol: str
    plant_id: str
    line_id: str
    operating_state: str
    health_state: str
    quality: str
    sequence: int
    latest_event_time: Optional[str] = None
    latest_ingestion_time: Optional[str] = None
    source_endpoint: Optional[str] = None
    source_address: Optional[str] = None
    signals: List[SignalMetadataItem] = Field(default_factory=list)
    current_measurements: Dict[str, Any] = Field(default_factory=dict)
    current_derived: Dict[str, Any] = Field(default_factory=dict)
