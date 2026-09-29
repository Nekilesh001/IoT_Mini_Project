"""
FastAPI route handlers for operational alert inspection, acknowledgment, and resolution.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from alerts.repository import AlertRepository
from alerts.service import AlertService
from api.dependencies import get_alert_repository
from api.schemas.alerts import (
    AcknowledgeRequest,
    AlertItem,
    AlertSummaryResponse,
    ResolveRequest,
)

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


def get_alert_service(
    repository: AlertRepository = Depends(get_alert_repository),
) -> AlertService:
    return AlertService(repository)


@router.get("", response_model=List[AlertItem], summary="List all historical and active alerts")
def list_alerts(
    machine_id: Optional[str] = Query(None, description="Filter by machine ID"),
    severity: Optional[str] = Query(None, description="Filter by severity (INFO, WARNING, CRITICAL)"),
    status: Optional[str] = Query(None, description="Filter by status (OPEN, ACKNOWLEDGED, RESOLVED)"),
    start: Optional[datetime] = Query(None, description="Start timestamp filter (ISO 8601)"),
    end: Optional[datetime] = Query(None, description="End timestamp filter (ISO 8601)"),
    limit: int = Query(100, ge=1, le=1000, description="Max alerts to return"),
    service: AlertService = Depends(get_alert_service),
):
    if start and end and start > end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start time must be before end time.",
        )
    return service.list_alerts(
        machine_id=machine_id,
        severity=severity,
        status=status,
        start=start,
        end=end,
        limit=limit,
    )


@router.get("/active", response_model=List[AlertItem], summary="List active (OPEN or ACKNOWLEDGED) alerts")
def list_active_alerts(
    limit: int = Query(200, ge=1, le=1000, description="Max active alerts to return"),
    service: AlertService = Depends(get_alert_service),
):
    return service.list_active_alerts(limit=limit)


@router.get("/summary", response_model=AlertSummaryResponse, summary="Get factory-wide alert operational summary")
def get_alert_summary(service: AlertService = Depends(get_alert_service)):
    return service.get_alert_summary()


@router.get("/{alert_id}", response_model=AlertItem, summary="Get alert detail by ID")
def get_alert_by_id(alert_id: str, service: AlertService = Depends(get_alert_service)):
    alert = service.get_alert_by_id(alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{alert_id}' not found.",
        )
    return alert


@router.post("/{alert_id}/acknowledge", response_model=AlertItem, summary="Acknowledge an active OPEN alert")
def acknowledge_alert(
    alert_id: str,
    payload: Optional[AcknowledgeRequest] = None,
    service: AlertService = Depends(get_alert_service),
):
    ack_by = payload.acknowledged_by if payload else "operator"
    try:
        updated = service.acknowledge_alert(alert_id, acknowledged_by=ack_by)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert '{alert_id}' not found.",
            )
        return updated
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{alert_id}/resolve", response_model=AlertItem, summary="Resolve an alert")
def resolve_alert(
    alert_id: str,
    payload: Optional[ResolveRequest] = None,
    service: AlertService = Depends(get_alert_service),
):
    notes = payload.resolution_notes if payload else "Resolved by operator"
    updated = service.resolve_alert(alert_id, resolution_notes=notes)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{alert_id}' not found.",
        )
    return updated
