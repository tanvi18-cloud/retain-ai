"""Structured Pydantic outputs for RetainAI agents."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import Field

from app.models.enums import RecommendationDecision
from app.schemas.common import APIModel, validate_confidence


class DataQuality(StrEnum):
    """Customer data completeness for agent reasoning."""

    GOOD = "GOOD"
    PARTIAL = "PARTIAL"
    POOR = "POOR"


class Urgency(StrEnum):
    """Recommended RM contact urgency."""

    IMMEDIATE = "IMMEDIATE"
    WITHIN_24_HOURS = "WITHIN_24_HOURS"
    WITHIN_3_DAYS = "WITHIN_3_DAYS"
    MONITOR = "MONITOR"
    NONE = "NONE"


class EvidenceReference(APIModel):
    """Source evidence supporting an agent claim."""

    source_system: str
    source_type: str
    reference_id: str | None = None
    field: str
    observed_value: Any
    timestamp: datetime | None = None


class SignalInvestigation(APIModel):
    """Signal Investigator structured output."""

    customer_id: str
    primary_signal: str
    primary_signal_source: str
    supporting_signals: list[str]
    counter_signals: list[str]
    data_quality: DataQuality
    missing_data: list[str]
    stale_data_sources: list[str]
    investigation_summary: str
    evidence_references: list[EvidenceReference]
    confidence: float = Field(ge=0, le=1)


class RetentionDecisionOutput(APIModel):
    """Retention Decision agent structured output."""

    customer_id: str
    deterministic_decision: RecommendationDecision
    agent_supported_decision: RecommendationDecision
    urgency: Urgency
    recommended_contact_window: str
    business_reason: str
    customer_value_context: str
    risks: list[str]
    policy_warnings: list[str]
    score_consistency_valid: bool
    confidence: float = Field(ge=0, le=1)


class OfferStrategyOutput(APIModel):
    """Offer Strategy agent structured output."""

    customer_id: str
    recommended_offer_id: str | None = None
    alternate_offer_id: str | None = None
    no_offer_reason: str | None = None
    offer_rationale: str
    scenario_fit: str
    estimated_offer_cost: float | None = None
    expected_retention_uplift: float | None = None
    expected_net_benefit: float | None = None
    financially_positive: bool | None = None
    eligibility_disclaimer: str
    policy_warnings: list[str]
    confidence: float = Field(ge=0, le=1)


class RMCopilotBrief(APIModel):
    """RM Copilot structured retention brief."""

    customer_id: str
    headline: str
    executive_summary: str
    why_now: str
    recommended_action: str
    talking_points: list[str]
    questions_to_ask_customer: list[str]
    prohibited_claims: list[str]
    next_steps: list[str]
    primary_offer_id: str | None = None
    financial_impact_summary: str
    evidence_references: list[EvidenceReference]
    confidence: float = Field(ge=0, le=1)


class AgentValidationResult(APIModel):
    """Result of post-agent policy validation."""

    valid: bool
    corrected: bool
    warnings: list[str]
    errors: list[str]
    validated_at: datetime


def validate_agent_confidence(value: float) -> float:
    """Validate agent confidence is within 0-1."""
    return validate_confidence(value)
