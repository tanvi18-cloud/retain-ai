"""RM alert records."""

from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.base import CreatedAtMixin, new_uuid
from app.models.enums import AlertType, NotificationStatus, Severity


class Alert(CreatedAtMixin, SQLModel, table=True):
    """Actionable alert assigned to a relationship manager."""

    __tablename__ = "alerts"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=36)
    customer_id: str = Field(
        foreign_key="customers.customer_id",
        nullable=False,
        index=True,
        max_length=32,
    )
    recommendation_id: str | None = Field(
        default=None,
        foreign_key="recommendations.id",
        nullable=True,
        max_length=36,
    )
    event_id: str | None = Field(
        default=None,
        foreign_key="incoming_events.id",
        nullable=True,
        index=True,
        max_length=36,
    )
    alert_type: AlertType = Field(default=AlertType.RULES_PREVIEW, nullable=False, index=True)
    severity: Severity = Field(nullable=False, index=True)
    title: str = Field(max_length=255, nullable=False)
    message: str = Field(max_length=2048, nullable=False)
    assigned_rm_id: str = Field(max_length=64, nullable=False, index=True)
    assigned_rm_email: str | None = Field(default=None, max_length=255, nullable=True)
    priority_score: int | None = Field(default=None, nullable=True)
    recommended_action: str | None = Field(default=None, max_length=1024, nullable=True)
    recommended_offer_id: str | None = Field(default=None, max_length=32, nullable=True)
    notification_status: NotificationStatus = Field(
        default=NotificationStatus.PENDING,
        nullable=False,
        index=True,
    )
    acknowledged: bool = Field(default=False, nullable=False, index=True)
    acknowledged_at: datetime | None = Field(default=None, nullable=True)
    acknowledged_by: str | None = Field(default=None, max_length=64, nullable=True)
