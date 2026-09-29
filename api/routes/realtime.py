"""
Server-Sent Events (SSE) realtime telemetry streaming endpoint.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from api.dependencies import get_telemetry_repository, get_factory_profiles, get_api_config
from api.services.realtime_service import RealtimeService

router = APIRouter(prefix="/api/realtime", tags=["Realtime"])


@router.get("/telemetry")
async def stream_realtime_telemetry(
    repo=Depends(get_telemetry_repository),
    profiles=Depends(get_factory_profiles),
    config=Depends(get_api_config)
):
    """
    Stream live telemetry events over Server-Sent Events (SSE).
    Clients receive events as new telemetry records are stored.
    """
    service = RealtimeService(
        repository=repo,
        profiles=profiles,
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
