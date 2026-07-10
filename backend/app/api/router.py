"""Central API router aggregating versioned route modules."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.health import build_health_response
from app.core.config import Settings, get_settings
from app.schemas.health import HealthResponse

api_router = APIRouter()


@api_router.get("/health", response_model=HealthResponse, tags=["health"])
def api_health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    """Versioned health check endpoint."""
    return build_health_response(settings)
