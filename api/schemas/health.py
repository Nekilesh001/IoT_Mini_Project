"""
Health and Protocol Health Schemas.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    database_connected: bool
    version: str = "1.0.0"
    timestamp: str


class ProtocolHealthItem(BaseModel):
    protocol: str
    status: str
    endpoint: str
    assigned_machines: List[str]
    last_seen: Optional[str] = None


class ProtocolHealthSummary(BaseModel):
    protocols: List[ProtocolHealthItem]
    total_protocols: int
    online_protocols: int
