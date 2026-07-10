"""Scoring response schemas."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import Field

from app.models.enums import RecommendationDecision
from app.schemas.common import APIModel


class ScoreBand(StrEnum):
    """Risk or value band derived from a score."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RuleContribution(APIModel):
    """Explainable contribution from a single scoring rule."""

    rule_code: str
    description: str
    points: float
    observed_value: Any
    source_system: str
    source_reference: str | None = None
    triggered: bool


class ScoreResult(APIModel):
    """Deterministic score with explainable contributions."""

    score: int = Field(ge=0, le=100)
    band: ScoreBand
    contributions: list[RuleContribution]
    calculation_version: str
    calculated_at: datetime


class PriorityResult(APIModel):
    """Retention priority derived from churn and value scores."""

    churn_score: int = Field(ge=0, le=100)
    value_score: int = Field(ge=0, le=100)
    churn_weight: float
    value_weight: float
    priority_score: int = Field(ge=0, le=100)
    decision: RecommendationDecision
    explanation: str
    calculation_version: str
    calculated_at: datetime
