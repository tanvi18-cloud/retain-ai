"""FastAPI handlers for domain and unhandled exceptions."""

from fastapi import FastAPI, Request
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from app.core.exceptions import DomainError
from app.core.logging import get_logger
from app.schemas.common import ApiError, ApiErrorResponse

logger = get_logger(__name__)


def _error_response(
    *,
    code: str,
    message: str,
    status_code: int,
    details: dict | None = None,
) -> JSONResponse:
    """Build a JSONResponse using the standard API error envelope."""
    payload = ApiErrorResponse(
        error=ApiError(code=code, message=message, details=details or {}),
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def register_exception_handlers(application: FastAPI) -> None:
    """Register application-wide exception handlers."""

    @application.exception_handler(DomainError)
    async def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
        return _error_response(
            code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details,
        )

    @application.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        _request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        return _error_response(
            code="HTTP_ERROR",
            message=str(exc.detail),
            status_code=exc.status_code,
        )

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "unhandled_exception",
            path=str(request.url.path),
            method=request.method,
        )
        return _error_response(
            code="INTERNAL_SERVER_ERROR",
            message="Internal server error",
            status_code=500,
        )
