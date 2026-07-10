"""Recommendation action API schemas."""

from datetime import date

from pydantic import Field

from app.schemas.common import APIModel


class RecommendationActionRequest(APIModel):
    """Common RM action payload."""

    rm_id: str = Field(min_length=1, max_length=64)
    notes: str | None = Field(default=None, max_length=2048)
    idempotency_key: str | None = Field(default=None, max_length=128)


class RecommendationRejectRequest(RecommendationActionRequest):
    """Reject recommendation payload."""

    rejection_reason: str = Field(min_length=1, max_length=1024)


class RecommendationContactedRequest(RecommendationActionRequest):
    """Contacted recommendation payload."""

    offer_presented: bool = False
    customer_response: str | None = Field(default=None, max_length=512)
    contact_channel: str | None = Field(default=None, max_length=32)
    follow_up_date: date | None = None


class RecommendationCloseRequest(RecommendationActionRequest):
    """Close recommendation payload."""

    closing_note: str = Field(min_length=1, max_length=1024)


class RecommendationActionResponse(APIModel):
    """Response after a recommendation workflow action."""

    recommendation_id: str
    status: str
    interaction_id: str
    message: str
