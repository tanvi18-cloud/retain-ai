"""Shared model utilities and mixins."""

import uuid
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(UTC)


def new_uuid() -> str:
    """Generate a new UUID string primary key."""
    return str(uuid.uuid4())


class TimestampMixin(SQLModel):
    """Created and updated timestamps for mutable entities."""

    created_at: datetime = Field(default_factory=utc_now, nullable=False, index=True)
    updated_at: datetime = Field(default_factory=utc_now, nullable=False)


class CreatedAtMixin(SQLModel):
    """Creation timestamp for append-only entities."""

    created_at: datetime = Field(default_factory=utc_now, nullable=False, index=True)
