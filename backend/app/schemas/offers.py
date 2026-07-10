"""Offer API schemas."""

from datetime import datetime

from pydantic import Field, field_validator

from app.schemas.common import APIModel, validate_non_negative_amount, validate_score


class OfferCreate(APIModel):
    """Payload for creating an offer."""

    offer_id: str = Field(min_length=1, max_length=32)
    product_type: str = Field(min_length=1, max_length=64)
    offer_name: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=1024)
    minimum_credit_score: int | None = None
    maximum_dpd: int = Field(ge=0)
    minimum_customer_value: float
    maximum_offer_cost: float
    estimated_cost: float
    expected_retention_uplift: float = Field(ge=0, le=1)
    active: bool = True
    requires_rm_approval: bool = False

    @field_validator(
        "minimum_customer_value",
        "maximum_offer_cost",
        "estimated_cost",
    )
    @classmethod
    def validate_amounts(cls, value: float) -> float:
        return validate_non_negative_amount(value)

    @field_validator("minimum_credit_score")
    @classmethod
    def validate_credit_score(cls, value: int | None) -> int | None:
        if value is None:
            return None
        validate_score(float(value))
        return value


class OfferUpdate(APIModel):
    """Payload for updating an offer."""

    offer_name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1, max_length=1024)
    minimum_credit_score: int | None = None
    maximum_dpd: int | None = Field(default=None, ge=0)
    minimum_customer_value: float | None = None
    maximum_offer_cost: float | None = None
    estimated_cost: float | None = None
    expected_retention_uplift: float | None = Field(default=None, ge=0, le=1)
    active: bool | None = None
    requires_rm_approval: bool | None = None


class OfferSummary(APIModel):
    """Compact offer representation."""

    offer_id: str
    product_type: str
    offer_name: str
    active: bool
    estimated_cost: float
    requires_rm_approval: bool


class OfferDetail(APIModel):
    """Full offer representation."""

    offer_id: str
    product_type: str
    offer_name: str
    description: str
    minimum_credit_score: int | None
    maximum_dpd: int
    minimum_customer_value: float
    maximum_offer_cost: float
    estimated_cost: float
    expected_retention_uplift: float
    active: bool
    requires_rm_approval: bool
    created_at: datetime
