"""Alert API schemas."""

from datetime import datetime

from pydantic import Field

from app.models.enums import AlertType, NotificationStatus, Severity
from app.schemas.common import APIModel


class AlertCreate(APIModel):
    """Payload for creating an alert."""

    customer_id: str = Field(min_length=1, max_length=32)
    recommendation_id: str | None = Field(default=None, max_length=36)
    event_id: str | None = Field(default=None, max_length=36)
    alert_type: AlertType = AlertType.RULES_PREVIEW
    severity: Severity
    title: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1, max_length=2048)
    assigned_rm_id: str = Field(min_length=1, max_length=64)
    acknowledged: bool = False


class AlertUpdate(APIModel):
    """Payload for updating an alert."""

    acknowledged: bool | None = None
    acknowledged_at: datetime | None = None
    notification_status: NotificationStatus | None = None


class AlertAcknowledgeRequest(APIModel):
    """Payload for acknowledging an alert."""

    rm_id: str = Field(min_length=1, max_length=64)
    note: str | None = Field(default=None, max_length=512)


class AlertSummary(APIModel):
    """Compact alert representation."""

    alert_id: str
    customer_id: str
    event_id: str | None
    recommendation_id: str | None
    alert_type: AlertType
    severity: Severity
    title: str
    priority_score: int | None
    acknowledged: bool
    notification_status: NotificationStatus
    created_at: datetime


class AlertDetail(APIModel):
    """Full alert representation."""

    alert_id: str
    customer_id: str
    event_id: str | None
    recommendation_id: str | None
    alert_type: AlertType
    severity: Severity
    title: str
    message: str
    assigned_rm_id: str
    assigned_rm_email: str | None
    priority_score: int | None
    recommended_action: str | None
    recommended_offer_id: str | None
    notification_status: NotificationStatus
    acknowledged: bool
    acknowledged_at: datetime | None
    acknowledged_by: str | None
    created_at: datetime


class RetentionAlertBroadcast(APIModel):
    """WebSocket retention alert payload."""

    type: str = "RETENTION_ALERT"
    alert_type: AlertType | None = None
    alert_id: str
    event_id: str | None
    recommendation_id: str | None = None
    customer_id: str
    severity: Severity
    title: str
    priority_score: int
    recommended_action: str
    recommended_offer: str | None = None
    expected_net_benefit: float | None = None
    created_at: datetime


class WebSocketConnectedMessage(APIModel):
    """WebSocket connection acknowledgement."""

    type: str = "CONNECTED"
    message: str
    timestamp: datetime


class WebSocketPongMessage(APIModel):
    """WebSocket heartbeat response."""

    type: str = "PONG"
    timestamp: datetime


class WebSocketPingMessage(APIModel):
    """WebSocket heartbeat request from client."""

    type: str = "PING"


class QueueStatusResponse(APIModel):
    """Async queue runtime metrics."""

    worker_count: int
    queue_size: int
    processing_count: int
    completed_count_since_startup: int
    failed_count_since_startup: int
    started_at: datetime


class NotificationStatusResponse(APIModel):
    """Safe notification subsystem configuration."""

    email_notifications_enabled: bool
    smtp_host: str
    smtp_port: int
    smtp_configured: bool
    websocket_connections: int
    alert_priority_threshold: int
