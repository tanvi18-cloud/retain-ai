"""Portfolio response schemas."""

from datetime import date, datetime

from pydantic import Field

from app.models.enums import CustomerSegment, RecommendationDecision
from app.schemas.common import APIModel


class PortfolioSummaryResponse(APIModel):
    """Portfolio-level retention summary."""

    total_customers: int
    immediate_intervention_count: int
    review_count: int
    monitor_count: int
    no_action_count: int
    total_revenue_at_risk: float
    total_positive_expected_net_benefit: float
    open_alerts: int
    unacknowledged_alerts: int
    high_value_high_risk_count: int
    generated_at: datetime


class PortfolioCustomerRow(APIModel):
    """Single customer row in the portfolio table."""

    customer_id: str
    full_name: str
    segment: CustomerSegment
    relationship_start_date: date
    churn_score: int = Field(ge=0, le=100)
    value_score: int = Field(ge=0, le=100)
    priority_score: int = Field(ge=0, le=100)
    decision: RecommendationDecision
    primary_trigger: str | None
    recommended_action: str
    top_eligible_offer_id: str | None
    top_eligible_offer_name: str | None
    revenue_at_risk: float
    expected_net_benefit: float | None
    recommendation_status: str | None
    has_data_warning: bool
    last_analyzed_at: datetime | None
