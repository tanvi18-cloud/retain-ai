"""System status API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.core.config import Settings, get_settings
from app.core.llm import get_llm_status
from app.schemas.alerts import NotificationStatusResponse, QueueStatusResponse
from app.schemas.llm import LLMStatus
from app.services.event_queue import EventQueue
from app.services.websocket_manager import WebSocketManager

router = APIRouter(prefix="/system", tags=["system"])


def _get_event_queue(request: Request) -> EventQueue:
    queue = getattr(request.app.state, "event_queue", None)
    if queue is None:
        msg = "Event queue is not initialized"
        raise RuntimeError(msg)
    return queue


def _get_websocket_manager(request: Request) -> WebSocketManager:
    manager = getattr(request.app.state, "websocket_manager", None)
    if manager is None:
        msg = "WebSocket manager is not initialized"
        raise RuntimeError(msg)
    return manager


@router.get(
    "/queue-status",
    response_model=QueueStatusResponse,
    summary="Get queue status",
)
def get_queue_status(
    request: Request,
) -> QueueStatusResponse:
    """Return async queue runtime metrics."""
    status = _get_event_queue(request).status()
    return QueueStatusResponse(**status)


@router.get(
    "/notification-status",
    response_model=NotificationStatusResponse,
    summary="Get notification status",
)
def get_notification_status(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> NotificationStatusResponse:
    """Return safe notification subsystem configuration."""
    manager = _get_websocket_manager(request)
    smtp_configured = bool(settings.smtp_host and settings.smtp_from)
    return NotificationStatusResponse(
        email_notifications_enabled=settings.email_notifications_enabled,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_configured=smtp_configured,
        websocket_connections=manager.connection_count,
        alert_priority_threshold=settings.alert_priority_threshold,
    )


@router.get(
    "/llm-status",
    response_model=LLMStatus,
    summary="Get LLM status",
)
def get_llm_status_endpoint(
    settings: Annotated[Settings, Depends(get_settings)],
) -> LLMStatus:
    """Return safe LLM subsystem status without exposing credentials."""
    return get_llm_status(settings)
