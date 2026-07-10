"""Approved retention offer catalog."""

from sqlmodel import Field, SQLModel

from app.models.base import CreatedAtMixin


class Offer(CreatedAtMixin, SQLModel, table=True):
    """Pre-approved retention offer available for recommendation."""

    __tablename__ = "offers"

    offer_id: str = Field(primary_key=True, max_length=32)
    product_type: str = Field(max_length=64, nullable=False)
    offer_name: str = Field(max_length=255, nullable=False)
    description: str = Field(max_length=1024, nullable=False)
    minimum_credit_score: int | None = Field(default=None, nullable=True)
    maximum_dpd: int = Field(nullable=False)
    minimum_customer_value: float = Field(nullable=False)
    maximum_offer_cost: float = Field(nullable=False)
    estimated_cost: float = Field(nullable=False)
    expected_retention_uplift: float = Field(nullable=False)
    active: bool = Field(default=True, nullable=False, index=True)
    requires_rm_approval: bool = Field(default=False, nullable=False)
