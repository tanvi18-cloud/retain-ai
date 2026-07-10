"""Notification delivery schemas."""

from datetime import datetime

from app.models.enums import NotificationStatus
from app.schemas.common import APIModel


class EmailDeliveryResult(APIModel):
    """Result of an email delivery attempt."""

    success: bool
    error: str | None = None
    preview_logged: bool = False


class NotificationResult(APIModel):
    """Structured notification delivery outcome."""

    alert_id: str
    websocket_attempted: bool
    websocket_success: bool
    websocket_connections_reached: int
    email_attempted: bool
    email_success: bool
    email_error: str | None = None
    final_status: NotificationStatus
    completed_at: datetime
