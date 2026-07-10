"""Concise Pydantic outputs for CrewAI read-only tools."""

from datetime import datetime

from app.models.enums import FreshnessStatus, RecommendationDecision
from app.schemas.analysis import OfferFinancialOption, RulesOnlyAnalysisResponse
from app.schemas.common import APIModel
from app.schemas.customer_360 import Customer360Response
from app.schemas.eligibility import EligibilityResult
from app.schemas.interactions import InteractionDetail
from app.schemas.offers import OfferDetail
from app.schemas.portfolio import PortfolioCustomerRow, PortfolioSummaryResponse


class Customer360ToolOutput(APIModel):
    """Concise Customer 360 payload for agent tools."""

    customer_id: str
    full_name: str
    segment: str
    estimated_annual_value: float
    communication_consent: bool
    account_count: int
    account_types: list[str]
    credit_score: int | None
    max_dpd_12m: int | None
    bureau_trigger_count: int
    bureau_trigger_summary: list[str]
    salary_received_current_month: bool | None
    balance_change_pct_30d: float | None
    external_transfer_amount_30d: float | None
    forex_spend_30d: float | None
    product_inactivity_days: int | None
    data_freshness: dict[str, FreshnessStatus]
    data_warnings: list[str]

    @classmethod
    def from_response(cls, response: Customer360Response) -> "Customer360ToolOutput":
        """Build a concise tool payload from Customer 360."""
        credit = response.credit_profile
        features = response.transaction_features
        freshness = {
            "core_banking": response.data_freshness.core_banking.status,
            "credit_history": response.data_freshness.credit_history.status,
            "bureau_triggers": response.data_freshness.bureau_triggers.status,
            "transaction_history": response.data_freshness.transaction_history.status,
        }
        trigger_summary = [
            f"{trigger.product_type}:{trigger.severity}:{trigger.trigger_type}"
            for trigger in response.bureau_triggers[:5]
        ]
        return cls(
            customer_id=response.customer.customer_id,
            full_name=response.customer.full_name,
            segment=response.customer.segment.value,
            estimated_annual_value=response.customer.estimated_annual_value,
            communication_consent=response.customer.communication_consent,
            account_count=len(response.accounts),
            account_types=sorted({account.account_type for account in response.accounts}),
            credit_score=credit.credit_score if credit else None,
            max_dpd_12m=credit.max_dpd_12m if credit else None,
            bureau_trigger_count=len(response.bureau_triggers),
            bureau_trigger_summary=trigger_summary,
            salary_received_current_month=(
                features.salary_received_current_month if features else None
            ),
            balance_change_pct_30d=features.balance_change_pct_30d if features else None,
            external_transfer_amount_30d=(
                features.external_transfer_amount_30d if features else None
            ),
            forex_spend_30d=features.forex_spend_30d if features else None,
            product_inactivity_days=features.product_inactivity_days if features else None,
            data_freshness=freshness,
            data_warnings=response.data_warnings,
        )


class CalculatedScoresToolOutput(APIModel):
    """Deterministic scoring payload for agent tools."""

    customer_id: str
    churn_score: int
    value_score: int
    priority_score: int
    decision: RecommendationDecision
    churn_band: str
    value_band: str
    triggered_rules: list[str]
    calculation_version: str
    calculated_at: datetime

    @classmethod
    def from_analysis(cls, analysis: RulesOnlyAnalysisResponse) -> "CalculatedScoresToolOutput":
        """Build scoring tool output from rules-only analysis."""
        triggered = [
            contribution.description
            for contribution in analysis.churn_result.contributions
            if contribution.triggered
        ]
        return cls(
            customer_id=analysis.customer_id,
            churn_score=analysis.churn_result.score,
            value_score=analysis.value_result.score,
            priority_score=analysis.priority_result.priority_score,
            decision=analysis.priority_result.decision,
            churn_band=analysis.churn_result.band.value,
            value_band=analysis.value_result.band.value,
            triggered_rules=triggered,
            calculation_version=analysis.churn_result.calculation_version,
            calculated_at=analysis.priority_result.calculated_at,
        )


class EligibleOffersToolOutput(APIModel):
    """Eligible and rejected offers for agent tools."""

    customer_id: str
    eligible_offers: list[dict]
    rejected_offers: list[dict]
    policy_warnings: list[str]
    evaluated_at: datetime

    @classmethod
    def from_eligibility(cls, result: EligibilityResult) -> "EligibleOffersToolOutput":
        """Build eligibility tool output."""
        return cls(
            customer_id=result.customer_id,
            eligible_offers=[
                {
                    "offer_id": offer.offer_id,
                    "offer_name": offer.offer_name,
                    "product_type": offer.product_type,
                    "estimated_cost": offer.estimated_cost,
                    "expected_retention_uplift": offer.expected_retention_uplift,
                }
                for offer in result.eligible_offers
            ],
            rejected_offers=[
                {
                    "offer_id": offer.offer_id,
                    "offer_name": offer.offer_name,
                    "reason_codes": offer.reason_codes,
                }
                for offer in result.rejected_offers
            ],
            policy_warnings=result.policy_warnings,
            evaluated_at=result.evaluated_at,
        )


class OfferToolOutput(APIModel):
    """Approved offer definition for agent tools."""

    offer_id: str
    offer_name: str
    product_type: str
    description: str
    maximum_dpd: int
    minimum_customer_value: float
    minimum_credit_score: int | None
    estimated_cost: float
    expected_retention_uplift: float
    active: bool
    requires_rm_approval: bool

    @classmethod
    def from_detail(cls, offer: OfferDetail) -> "OfferToolOutput":
        """Build offer tool output."""
        return cls(
            offer_id=offer.offer_id,
            offer_name=offer.offer_name,
            product_type=offer.product_type,
            description=offer.description,
            maximum_dpd=offer.maximum_dpd,
            minimum_customer_value=offer.minimum_customer_value,
            minimum_credit_score=offer.minimum_credit_score,
            estimated_cost=offer.estimated_cost,
            expected_retention_uplift=offer.expected_retention_uplift,
            active=offer.active,
            requires_rm_approval=offer.requires_rm_approval,
        )


class InteractionsToolOutput(APIModel):
    """Recent customer interactions for agent tools."""

    customer_id: str
    interactions: list[InteractionDetail]


class PortfolioMetricsToolOutput(APIModel):
    """Portfolio summary metrics for agent tools."""

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

    @classmethod
    def from_summary(cls, summary: PortfolioSummaryResponse) -> "PortfolioMetricsToolOutput":
        """Build portfolio metrics tool output."""
        return cls(
            total_customers=summary.total_customers,
            immediate_intervention_count=summary.immediate_intervention_count,
            review_count=summary.review_count,
            monitor_count=summary.monitor_count,
            no_action_count=summary.no_action_count,
            total_revenue_at_risk=summary.total_revenue_at_risk,
            total_positive_expected_net_benefit=summary.total_positive_expected_net_benefit,
            open_alerts=summary.open_alerts,
            unacknowledged_alerts=summary.unacknowledged_alerts,
            high_value_high_risk_count=summary.high_value_high_risk_count,
            generated_at=summary.generated_at,
        )


class PriorityCustomersToolOutput(APIModel):
    """Highest-priority customers for agent tools."""

    customers: list[PortfolioCustomerRow]


class FinancialOptionsToolOutput(APIModel):
    """Eligible financial options for agent tools."""

    customer_id: str
    options: list[OfferFinancialOption]

    @classmethod
    def from_analysis(cls, analysis: RulesOnlyAnalysisResponse) -> "FinancialOptionsToolOutput":
        """Build financial options tool output."""
        return cls(
            customer_id=analysis.customer_id,
            options=analysis.financial_options,
        )
