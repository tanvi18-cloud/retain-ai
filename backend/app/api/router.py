"""Central API router aggregating versioned route modules."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.analysis import router as analysis_router
from app.api.customers import router as customers_router
from app.api.health import build_health_response
from app.api.portfolio import router as portfolio_router
from app.api.recommendations import router as recommendations_router
from app.core.config import Settings, get_settings
from app.schemas.health import HealthResponse

api_router = APIRouter()
api_router.include_router(customers_router)
api_router.include_router(analysis_router)
api_router.include_router(portfolio_router)
api_router.include_router(recommendations_router)


@api_router.get("/health", response_model=HealthResponse, tags=["health"])
def api_health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    """Versioned health check endpoint."""
    return build_health_response(settings)
