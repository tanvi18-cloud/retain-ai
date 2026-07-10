"""Incoming event API schemas."""

from datetime import datetime
from typing import Any

from pydantic import Field

from app.models.enums import IncomingEventStatus
from app.schemas.common import APIModel


class IncomingEventCreate(APIModel):
    """Payload for creating an incoming event."""

    customer_id: str = Field(min_length=1, max_length=32)
    event_type: str = Field(min_length=1, max_length=64)
    source_system: str = Field(min_length=1, max_length=128)
    payload_json: dict[str, Any] = Field(default_factory=dict)
    status: IncomingEventStatus = IncomingEventStatus.RECEIVED


class IncomingEventUpdate(APIModel):
    """Payload for updating an incoming event."""

    status: IncomingEventStatus | None = None
    error_message: str | None = Field(default=None, max_length=2048)
    processed_at: datetime | None = None


class IncomingEventSummary(APIModel):
    """Compact incoming event representation."""

    event_id: str
    customer_id: str
    event_type: str
    source_system: str
    status: IncomingEventStatus
    created_at: datetime


class IncomingEventDetail(APIModel):
    """Full incoming event representation."""

    event_id: str
    customer_id: str
    event_type: str
    source_system: str
    payload_json: dict[str, Any]
    status: IncomingEventStatus
    error_message: str | None
    created_at: datetime
    processed_at: datetime | None
