"""
Pydantic schemas for Fault Scenario management endpoints.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FaultScenarioItem(BaseModel):
    scenario_id: str = Field(..., description="Unique scenario ID")
    machine_id: str = Field(..., description="Target machine ID")
    machine_type: str = Field(..., description="Machine type")
    fault_type: str = Field(..., description="Fault taxonomy category")
    fault_code: str = Field(..., description="Machine fault code")
    title: str = Field(..., description="Scenario title")
    description: str = Field(..., description="Physical description of fault")
    severity: str = Field(..., description="Alert severity: INFO, WARNING, CRITICAL")
    is_progressive: bool = Field(..., description="Whether degradation increases over time")
    duration_ticks: Optional[int] = Field(None, description="Optional auto-resolution tick limit")
    state: str = Field(..., description="Lifecycle state: IDLE, ACTIVE, RESOLVED")
    current_tick: int = Field(0, description="Elapsed ticks under active condition")
    start_time: Optional[str] = Field(None, description="ISO activation timestamp")
    end_time: Optional[str] = Field(None, description="ISO resolution timestamp")
