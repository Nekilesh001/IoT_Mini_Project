"""
Factory Summary Schemas.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from api.schemas.health import ProtocolHealthItem


class StateCountSummary(BaseModel):
    running: int = 0
    idle: int = 0
    starting: int = 0
    stopping: int = 0
    maintenance: int = 0
    off: int = 0


class HealthCountSummary(BaseModel):
    healthy: int = 0
    warning: int = 0
    critical: int = 0


class FactorySummaryResponse(BaseModel):
    total_machines: int
    states: StateCountSummary
    health: HealthCountSummary
    protocols: List[ProtocolHealthItem]
    total_telemetry_records: int
    latest_event_time: Optional[str] = None
