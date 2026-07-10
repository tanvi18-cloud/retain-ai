"""Offer eligibility response schemas."""

from datetime import datetime

from pydantic import Field

from app.schemas.common import APIModel


class EligibilityReason(APIModel):
    """Reason an offer passed eligibility checks."""

    code: str
    description: str
    observed_value: str | None = None


class EligibleOffer(APIModel):
    """Offer eligible for RM discussion."""

    offer_id: str
    offer_name: str
    product_type: str
    description: str
    estimated_cost: float = Field(ge=0)
    expected_retention_uplift: float = Field(ge=0, le=1)
    eligibility_reasons: list[EligibilityReason]
    requires_rm_approval: bool


class RejectedOffer(APIModel):
    """Offer rejected by deterministic policy rules."""

    offer_id: str
    offer_name: str
    product_type: str
    reason_codes: list[str]
    explanations: list[str]


class EligibilityResult(APIModel):
    """Deterministic eligibility evaluation for a customer."""

    customer_id: str
    eligible_offers: list[EligibleOffer]
    rejected_offers: list[RejectedOffer]
    policy_warnings: list[str]
    policy_version: str
    evaluated_at: datetime
