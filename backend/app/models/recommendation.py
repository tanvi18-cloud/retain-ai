"""Retention recommendation records."""

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from app.models.base import TimestampMixin, new_uuid
from app.models.enums import CreatedByMode, RecommendationDecision, RecommendationStatus


class Recommendation(TimestampMixin, SQLModel, table=True):
    """Scored retention recommendation for a customer."""

    __tablename__ = "recommendations"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=36)
    customer_id: str = Field(
        foreign_key="customers.customer_id",
        nullable=False,
        index=True,
        max_length=32,
    )
    triggering_event_id: str | None = Field(
        default=None,
        foreign_key="incoming_events.id",
        nullable=True,
        max_length=36,
        index=True,
    )
    analysis_execution_id: str | None = Field(
        default=None,
        foreign_key="analysis_executions.id",
        nullable=True,
        max_length=36,
        index=True,
    )
    churn_score: float = Field(nullable=False)
    value_score: float = Field(nullable=False)
    priority_score: float = Field(nullable=False, index=True)
    decision: RecommendationDecision = Field(nullable=False)
    recommended_offer_id: str | None = Field(
        default=None,
        foreign_key="offers.offer_id",
        nullable=True,
        max_length=32,
    )
    alternate_offer_id: str | None = Field(
        default=None,
        foreign_key="offers.offer_id",
        nullable=True,
        max_length=32,
    )
    revenue_at_risk: float = Field(nullable=False)
    expected_net_benefit: float = Field(nullable=False)
    confidence: float = Field(nullable=False)
    summary: str = Field(max_length=2048, nullable=False)
    investigation_summary: str | None = Field(default=None, max_length=2048, nullable=True)
    created_by_mode: CreatedByMode = Field(default=CreatedByMode.RULES_ONLY, nullable=False)
    calculation_version: str | None = Field(default=None, max_length=64, nullable=True)
    policy_version: str | None = Field(default=None, max_length=64, nullable=True)
    evidence_json: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    rm_brief_json: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    policy_warnings_json: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    validation_warnings_json: list = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    status: RecommendationStatus = Field(
        default=RecommendationStatus.NEW,
        nullable=False,
        index=True,
    )
