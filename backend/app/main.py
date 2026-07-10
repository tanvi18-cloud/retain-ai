"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import build_health_response
from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.database import configure_engine, init_db
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.schemas.health import HealthResponse

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan hook for startup and shutdown logging."""
    settings: Settings = app.state.settings
    logger.info(
        "application_startup",
        app_name=settings.app_name,
        environment=settings.app_env,
        version=settings.api_version,
        debug=settings.debug,
    )
    init_db()
    logger.info("database_initialized", database_url=settings.database_url)
    yield
    logger.info(
        "application_shutdown",
        app_name=settings.app_name,
        environment=settings.app_env,
        version=settings.api_version,
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    resolved_settings = settings or get_settings()
    configure_logging(debug=resolved_settings.debug)
    configure_engine(resolved_settings.database_url)

    application = FastAPI(
        title=resolved_settings.app_name,
        version=resolved_settings.api_version,
        lifespan=lifespan,
    )
    application.state.settings = resolved_settings

    application.add_middleware(
        CORSMiddleware,
        allow_origins=[resolved_settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get("/health", response_model=HealthResponse, tags=["health"])
    def root_health(
        current_settings: Annotated[Settings, Depends(get_settings)],
    ) -> HealthResponse:
        """Root health check endpoint."""
        return build_health_response(current_settings)

    application.include_router(api_router, prefix="/api/v1")
    register_exception_handlers(application)

    return application


app = create_app()
