"""Rules-only analysis response schemas."""

from datetime import datetime

from app.models.enums import CustomerSegment
from app.schemas.common import APIModel
from app.schemas.eligibility import EligibilityResult
from app.schemas.scoring import PriorityResult, ScoreResult


class OfferFinancialOption(APIModel):
    """Financial projection for an eligible offer."""

    offer_id: str
    offer_name: str
    product_type: str
    financials: "RetentionFinancials"


class RetentionFinancials(APIModel):
    """Financial retention estimate for a customer or offer."""

    annual_customer_value: float
    churn_probability: float
    revenue_at_risk: float
    expected_retention_uplift: float
    estimated_offer_cost: float
    expected_gross_retention_value: float
    expected_net_benefit: float
    financially_positive: bool
    assumptions: list[str]
    calculated_at: datetime


class RulesOnlyAnalysisResponse(APIModel):
    """Synchronous rules-only customer analysis."""

    customer_id: str
    customer_name: str
    customer_segment: CustomerSegment
    customer_360_warnings: list[str]
    churn_result: ScoreResult
    value_result: ScoreResult
    priority_result: PriorityResult
    eligibility_result: EligibilityResult
    financial_options: list[OfferFinancialOption]
    top_risk_signals: list[str]
    primary_trigger: str | None
    suggested_action: str
    generated_at: datetime
    analysis_version: str


OfferFinancialOption.model_rebuild()
