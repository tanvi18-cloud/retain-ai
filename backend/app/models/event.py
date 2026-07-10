"""Inbound customer event records."""

from datetime import datetime

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.base import CreatedAtMixin, new_uuid
from app.models.enums import IncomingEventStatus


class IncomingEvent(CreatedAtMixin, SQLModel, table=True):
    """Event received from upstream banking systems for async processing."""

    __tablename__ = "incoming_events"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_incoming_events_idempotency_key"),
    )

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=36)
    customer_id: str = Field(
        foreign_key="customers.customer_id",
        nullable=False,
        index=True,
        max_length=32,
    )
    event_type: str = Field(max_length=64, nullable=False, index=True)
    source_system: str = Field(max_length=128, nullable=False, index=True)
    payload_json: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    idempotency_key: str | None = Field(default=None, max_length=128, nullable=True, index=True)
    execution_id: str | None = Field(default=None, max_length=36, nullable=True)
    analysis_result_json: dict | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    status: IncomingEventStatus = Field(
        default=IncomingEventStatus.RECEIVED,
        nullable=False,
        index=True,
    )
    error_message: str | None = Field(default=None, max_length=2048, nullable=True)
    retry_count: int = Field(default=0, nullable=False)
    notifications_enabled: bool = Field(default=True, nullable=False)
    queued_at: datetime | None = Field(default=None, nullable=True)
    processing_started_at: datetime | None = Field(default=None, nullable=True)
    processed_at: datetime | None = Field(default=None, nullable=True)
