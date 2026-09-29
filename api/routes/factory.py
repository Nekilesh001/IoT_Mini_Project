"""
Factory Summary operational routes.
"""

from fastapi import APIRouter, Depends
from api.dependencies import get_telemetry_repository, get_factory_profiles
from api.schemas.factory import FactorySummaryResponse
from api.services.factory_service import FactoryService

router = APIRouter(prefix="/api/factory", tags=["Factory"])


@router.get("/summary", response_model=FactorySummaryResponse)
def get_factory_summary(
    repo=Depends(get_telemetry_repository),
    profiles=Depends(get_factory_profiles)
):
    """High-level operational summary of factory machines, states, and telemetry counts."""
    service = FactoryService(repository=repo, profiles=profiles)
    return service.get_factory_summary()
