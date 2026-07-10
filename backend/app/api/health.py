"""Health check endpoint handlers."""

from app.core.config import Settings
from app.schemas.health import HealthResponse


def build_health_response(settings: Settings) -> HealthResponse:
    """Build the standard health check response from application settings."""
    return HealthResponse(
        status="healthy",
        service="RetainAI API",
        environment=settings.app_env,
        version=settings.api_version,
    )
