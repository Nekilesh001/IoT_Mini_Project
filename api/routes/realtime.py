"""
Server-Sent Events (SSE) realtime telemetry and alert streaming endpoints.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from api.dependencies import (
    get_telemetry_repository,
    get_alert_repository,
    get_ml_repository,
    get_factory_profiles,
    get_api_config,
)
from api.services.realtime_service import RealtimeService

router = APIRouter(prefix="/api/realtime", tags=["Realtime"])


@router.get("/telemetry")
async def stream_realtime_telemetry(
    repo=Depends(get_telemetry_repository),
    alert_repo=Depends(get_alert_repository),
    ml_repo=Depends(get_ml_repository),
    profiles=Depends(get_factory_profiles),
    config=Depends(get_api_config)
):
    """
    Stream live telemetry events, operational alerts, and ML predictions over Server-Sent Events (SSE).
    """
    service = RealtimeService(
        repository=repo,
        profiles=profiles,
        alert_repository=alert_repo,
        ml_repository=ml_repo,
        interval_seconds=config.realtime_interval_seconds
    )

    return StreamingResponse(
        service.event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/alerts")
async def stream_realtime_alerts(
    alert_repo=Depends(get_alert_repository),
    repo=Depends(get_telemetry_repository),
    profiles=Depends(get_factory_profiles),
    config=Depends(get_api_config)
):
    """
    Dedicated SSE stream for active alert updates.
    """
    service = RealtimeService(
        repository=repo,
        profiles=profiles,
        alert_repository=alert_repo,
        interval_seconds=config.realtime_interval_seconds
    )

    return StreamingResponse(
        service.alert_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no"
        }
    )
