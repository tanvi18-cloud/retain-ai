"""Alert API schemas."""

from datetime import datetime

from pydantic import Field

from app.models.enums import Severity
from app.schemas.common import APIModel


class AlertCreate(APIModel):
    """Payload for creating an alert."""

    customer_id: str = Field(min_length=1, max_length=32)
    recommendation_id: str = Field(min_length=1, max_length=36)
    severity: Severity
    title: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1, max_length=2048)
    assigned_rm_id: str = Field(min_length=1, max_length=64)
    acknowledged: bool = False


class AlertUpdate(APIModel):
    """Payload for updating an alert."""

    acknowledged: bool | None = None
    acknowledged_at: datetime | None = None


class AlertSummary(APIModel):
    """Compact alert representation."""

    alert_id: str
    customer_id: str
    recommendation_id: str
    severity: Severity
    title: str
    acknowledged: bool
    created_at: datetime


class AlertDetail(APIModel):
    """Full alert representation."""

    alert_id: str
    customer_id: str
    recommendation_id: str
    severity: Severity
    title: str
    message: str
    assigned_rm_id: str
    acknowledged: bool
    acknowledged_at: datetime | None
    created_at: datetime
