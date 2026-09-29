"""
Health check and Protocol status routes.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import text

from api.dependencies import get_db_engine, get_telemetry_repository, get_factory_profiles
from api.schemas.health import HealthResponse, ProtocolHealthSummary
from api.services.factory_service import FactoryService

router = APIRouter(tags=["Health"])


@router.get("/api/health", response_model=HealthResponse)
def get_health(engine=Depends(get_db_engine)):
    """API health status and database connectivity check."""
    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        db_ok = False

    return HealthResponse(
        status="ok" if db_ok else "degraded",
        database_connected=db_ok,
        version="1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat()
    )


@router.get("/api/protocols/health", response_model=ProtocolHealthSummary)
def get_protocol_health(
    repo=Depends(get_telemetry_repository),
    profiles=Depends(get_factory_profiles)
):
    """Current protocol status and assigned machine list."""
    service = FactoryService(repository=repo, profiles=profiles)
    return service.get_protocol_health_summary()
