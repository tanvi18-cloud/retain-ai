"""Interaction API schemas."""

from datetime import datetime

from pydantic import Field

from app.schemas.common import APIModel


class InteractionCreate(APIModel):
    """Payload for creating an interaction."""

    customer_id: str = Field(min_length=1, max_length=32)
    recommendation_id: str | None = Field(default=None, max_length=36)
    rm_id: str = Field(min_length=1, max_length=64)
    action_type: str = Field(min_length=1, max_length=64)
    notes: str | None = Field(default=None, max_length=2048)
    offer_presented: bool = False
    customer_response: str | None = Field(default=None, max_length=512)


class InteractionUpdate(APIModel):
    """Payload for updating an interaction."""

    notes: str | None = Field(default=None, max_length=2048)
    offer_presented: bool | None = None
    customer_response: str | None = Field(default=None, max_length=512)


class InteractionSummary(APIModel):
    """Compact interaction representation."""

    interaction_id: str
    customer_id: str
    recommendation_id: str | None
    rm_id: str
    action_type: str
    offer_presented: bool
    created_at: datetime


class InteractionDetail(APIModel):
    """Full interaction representation."""

    interaction_id: str
    customer_id: str
    recommendation_id: str | None
    rm_id: str
    action_type: str
    notes: str | None
    offer_presented: bool
    customer_response: str | None
    created_at: datetime
