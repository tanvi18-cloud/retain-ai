"""Relationship manager interaction records."""

from datetime import date

from sqlmodel import Field, SQLModel

from app.models.base import CreatedAtMixin, new_uuid


class Interaction(CreatedAtMixin, SQLModel, table=True):
    """Logged RM outreach or customer contact activity."""

    __tablename__ = "interactions"

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
    rm_id: str = Field(max_length=64, nullable=False)
    action_type: str = Field(max_length=64, nullable=False)
    notes: str | None = Field(default=None, max_length=2048, nullable=True)
    offer_presented: bool = Field(default=False, nullable=False)
    customer_response: str | None = Field(default=None, max_length=512, nullable=True)
    contact_channel: str | None = Field(default=None, max_length=32, nullable=True)
    follow_up_date: date | None = Field(default=None, nullable=True)
    idempotency_key: str | None = Field(default=None, max_length=128, nullable=True, index=True)
