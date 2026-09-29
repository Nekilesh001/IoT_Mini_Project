"""
Pydantic schemas for Alert REST endpoints.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AlertItem(BaseModel):
    alert_id: str = Field(..., description="Unique alert UUID")
    rule_id: str = Field(..., description="Triggered alert rule ID")
    machine_id: str = Field(..., description="Associated machine ID")
    machine_type: str = Field(..., description="Machine type identifier")
    alert_code: str = Field(..., description="Standard operational alert code")
    severity: str = Field(..., description="Severity level: INFO, WARNING, CRITICAL")
    title: str = Field(..., description="Human-readable alert title")
    description: str = Field(..., description="Explanation of the triggered anomaly condition")
    status: str = Field(..., description="Lifecycle status: OPEN, ACKNOWLEDGED, RESOLVED")
    triggered_at: str = Field(..., description="ISO timestamp when the alert first triggered")
    acknowledged_at: Optional[str] = Field(None, description="ISO timestamp of acknowledgment")
    acknowledged_by: Optional[str] = Field(None, description="Operator identifier")
    resolved_at: Optional[str] = Field(None, description="ISO timestamp of resolution")
    resolution_notes: Optional[str] = Field(None, description="Operator or auto-clear resolution notes")
    triggering_measurements: Dict[str, Any] = Field(..., description="Observed sensor values at trigger time")
    current_measurements: Optional[Dict[str, Any]] = Field(None, description="Most recent sensor values")
    occurrence_count: int = Field(1, description="Number of times rule condition was observed while active")
    last_occurrence_at: Optional[str] = Field(None, description="ISO timestamp of most recent trigger tick")


class AlertSummaryResponse(BaseModel):
    active_total: int = Field(..., description="Total active (OPEN or ACKNOWLEDGED) alerts")
    open_total: int = Field(..., description="Total unacknowledged OPEN alerts")
    acknowledged_total: int = Field(..., description="Total ACKNOWLEDGED alerts")
    critical_count: int = Field(..., description="Total active CRITICAL severity alerts")
    warning_count: int = Field(..., description="Total active WARNING severity alerts")
    info_count: int = Field(..., description="Total active INFO severity alerts")
    active_machines_count: Optional[int] = Field(None, description="Number of distinct machines with active alerts")
    machines_with_active_alerts: Optional[int] = Field(None, description="Number of distinct machines with active alerts")
    active_machines: Optional[List[str]] = Field(None, description="List of machine IDs with active alerts")
    total_historical_alerts: Optional[int] = Field(None, description="Total lifetime recorded alerts")
    recent_alert_count: Optional[int] = Field(None, description="Recent alert count")
    timestamp: str = Field(..., description="ISO calculation timestamp")


class AcknowledgeRequest(BaseModel):
    acknowledged_by: Optional[str] = Field("operator", description="Identifier of the operator acknowledging the alert")


class ResolveRequest(BaseModel):
    resolution_notes: Optional[str] = Field("Resolved by operator", description="Notes explaining fault resolution")


AlertResponse = AlertItem
