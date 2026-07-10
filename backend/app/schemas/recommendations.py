"""Recommendation read API schemas."""

from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from app.core.policy_rules import ELIGIBILITY_DISCLAIMER
from app.models.enums import CreatedByMode, RecommendationDecision, RecommendationStatus
from app.schemas.common import (
    APIModel,
    validate_confidence,
    validate_non_negative_amount,
    validate_score,
)
from app.schemas.interactions import InteractionDetail


class RecommendationCreate(APIModel):
    """Payload for creating a recommendation."""

    customer_id: str = Field(min_length=1, max_length=32)
    triggering_event_id: str | None = Field(default=None, max_length=36)
    churn_score: float
    value_score: float
    priority_score: float
    decision: RecommendationDecision
    recommended_offer_id: str | None = Field(default=None, max_length=32)
    alternate_offer_id: str | None = Field(default=None, max_length=32)
    revenue_at_risk: float
    expected_net_benefit: float
    confidence: float
    summary: str = Field(min_length=1, max_length=2048)
    evidence_json: dict[str, Any] = Field(default_factory=dict)
    status: RecommendationStatus = RecommendationStatus.NEW

    @field_validator("churn_score", "value_score", "priority_score")
    @classmethod
    def validate_scores(cls, value: float) -> float:
        return validate_score(value)

    @field_validator("confidence")
    @classmethod
    def validate_confidence_value(cls, value: float) -> float:
        return validate_confidence(value)

    @field_validator("revenue_at_risk", "expected_net_benefit")
    @classmethod
    def validate_amounts(cls, value: float) -> float:
        return validate_non_negative_amount(value)


class RecommendationUpdate(APIModel):
    """Payload for updating a recommendation."""

    decision: RecommendationDecision | None = None
    recommended_offer_id: str | None = Field(default=None, max_length=32)
    alternate_offer_id: str | None = Field(default=None, max_length=32)
    summary: str | None = Field(default=None, min_length=1, max_length=2048)
    evidence_json: dict[str, Any] | None = None
    status: RecommendationStatus | None = None


class RecommendationSummary(APIModel):
    """Compact recommendation representation."""

    recommendation_id: str
    customer_id: str
    churn_score: float
    value_score: float
    priority_score: float
    decision: RecommendationDecision
    status: RecommendationStatus
    recommended_offer_id: str | None


class RecommendationDetail(APIModel):
    """Full recommendation representation."""

    recommendation_id: str
    customer_id: str
    triggering_event_id: str | None
    analysis_execution_id: str | None = None
    churn_score: float
    value_score: float
    priority_score: float
    decision: RecommendationDecision
    recommended_offer_id: str | None
    alternate_offer_id: str | None
    revenue_at_risk: float
    expected_net_benefit: float
    confidence: float
    summary: str
    investigation_summary: str | None = None
    evidence_json: dict[str, Any]
    rm_brief_json: dict[str, Any] = Field(default_factory=dict)
    policy_warnings_json: list[str] = Field(default_factory=list)
    validation_warnings_json: list[str] = Field(default_factory=list)
    created_by_mode: CreatedByMode = CreatedByMode.RULES_ONLY
    calculation_version: str | None = None
    policy_version: str | None = None
    eligibility_disclaimer: str = ELIGIBILITY_DISCLAIMER
    status: RecommendationStatus
    created_at: datetime
    updated_at: datetime
    interactions: list[InteractionDetail] = Field(default_factory=list)
