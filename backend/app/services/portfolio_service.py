"""Portfolio aggregation service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from sqlmodel import Session

from app.core.exceptions import UnsupportedSortFieldError
from app.core.scoring_rules import CHURN_BAND_HIGH_MAX
from app.models.enums import CustomerSegment, RecommendationDecision
from app.schemas.analysis import RulesOnlyAnalysisResponse
from app.schemas.common import PaginatedResponse
from app.schemas.portfolio import PortfolioCustomerRow, PortfolioSummaryResponse
from app.schemas.recommendations import RecommendationSummary
from app.services.alert_repository import AlertRepository
from app.services.analysis_service import AnalysisService
from app.services.customer_repository import CustomerRepository
from app.services.recommendation_repository import RecommendationRepository
from app.services.repository_utils import validate_pagination

PortfolioSortField = Literal[
    "customer_id",
    "full_name",
    "churn_score",
    "value_score",
    "priority_score",
    "revenue_at_risk",
    "expected_net_benefit",
]
SortOrder = Literal["asc", "desc"]


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _revenue_at_risk(analysis: RulesOnlyAnalysisResponse, annual_value: float) -> float:
    if analysis.financial_options:
        return analysis.financial_options[0].financials.revenue_at_risk
    churn_probability = analysis.churn_result.score / 100
    return round(annual_value * churn_probability, 2)


class PortfolioService:
    """Build portfolio summary and customer table views."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.customers = CustomerRepository(session)
        self.analysis_service = AnalysisService(session)
        self.recommendations = RecommendationRepository(session)
        self.alerts = AlertRepository(session)

    def _analyze_customer(
        self,
        customer_id: str,
    ) -> tuple[RulesOnlyAnalysisResponse, RecommendationSummary | None]:
        analysis = self.analysis_service.analyze_customer_rules_only(customer_id)
        saved = self.recommendations.list_all_by_customer(customer_id)
        return analysis, saved[0] if saved else None

    def get_summary(self) -> PortfolioSummaryResponse:
        """Calculate portfolio summary across all customers."""
        customer_page = self.customers.list_customers(page=1, page_size=100)
        rows = [
            self._build_row(
                self.customers.get_by_id(customer.customer_id),
                *self._analyze_customer(customer.customer_id),
            )
            for customer in customer_page.items
        ]

        retain_count = sum(1 for row in rows if row.decision == RecommendationDecision.RETAIN)
        review_count = sum(1 for row in rows if row.decision == RecommendationDecision.REVIEW)
        monitor_count = sum(1 for row in rows if row.decision == RecommendationDecision.MONITOR)
        no_action_count = sum(1 for row in rows if row.decision == RecommendationDecision.NO_ACTION)

        return PortfolioSummaryResponse(
            total_customers=len(rows),
            immediate_intervention_count=retain_count,
            review_count=review_count,
            monitor_count=monitor_count,
            no_action_count=no_action_count,
            total_revenue_at_risk=round(sum(row.revenue_at_risk for row in rows), 2),
            total_positive_expected_net_benefit=round(
                sum(
                    row.expected_net_benefit or 0
                    for row in rows
                    if (row.expected_net_benefit or 0) > 0
                ),
                2,
            ),
            open_alerts=self.alerts.count_all(),
            unacknowledged_alerts=self.alerts.count_unacknowledged(),
            high_value_high_risk_count=sum(
                1
                for row in rows
                if row.churn_score > CHURN_BAND_HIGH_MAX and row.value_score > CHURN_BAND_HIGH_MAX
            ),
            generated_at=_utc_now(),
        )

    def list_customers(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        segment: CustomerSegment | None = None,
        decision: RecommendationDecision | None = None,
        trigger_type: str | None = None,
        minimum_priority: int | None = None,
        sort_by: PortfolioSortField = "priority_score",
        sort_order: SortOrder = "desc",
    ) -> PaginatedResponse[PortfolioCustomerRow]:
        """Return paginated portfolio customer rows."""
        validate_pagination(page, page_size)
        allowed_sort_fields = {
            "customer_id",
            "full_name",
            "churn_score",
            "value_score",
            "priority_score",
            "revenue_at_risk",
            "expected_net_benefit",
        }
        if sort_by not in allowed_sort_fields:
            raise UnsupportedSortFieldError(
                message=f"Unsupported sort field: {sort_by}",
                details={"sort_by": sort_by},
            )

        customer_page = self.customers.list_customers(
            page=1,
            page_size=100,
            segment=segment,
            search=search,
        )
        rows: list[PortfolioCustomerRow] = []
        for customer_summary in customer_page.items:
            customer = self.customers.get_by_id(customer_summary.customer_id)
            analysis, saved = self._analyze_customer(customer.customer_id)
            row = self._build_row(customer, analysis, saved)
            if decision is not None and row.decision != decision:
                continue
            if minimum_priority is not None and row.priority_score < minimum_priority:
                continue
            if trigger_type is not None and row.primary_trigger != trigger_type:
                continue
            rows.append(row)

        reverse = sort_order == "desc"

        def sort_key(row: PortfolioCustomerRow):
            value = getattr(row, sort_by)
            if value is None:
                return float("-inf") if reverse else float("inf")
            return value

        rows.sort(key=sort_key, reverse=reverse)
        offset = (page - 1) * page_size
        return PaginatedResponse.build(
            items=rows[offset : offset + page_size],
            total=len(rows),
            page=page,
            page_size=page_size,
        )

    @staticmethod
    def _build_row(customer, analysis, saved) -> PortfolioCustomerRow:
        """Build a portfolio row from analysis output."""
        top_financial = analysis.financial_options[0] if analysis.financial_options else None
        top_eligible = None
        if top_financial is not None:
            top_eligible = next(
                (
                    offer
                    for offer in analysis.eligibility_result.eligible_offers
                    if offer.offer_id == top_financial.offer_id
                ),
                None,
            )
        elif analysis.eligibility_result.eligible_offers:
            top_eligible = analysis.eligibility_result.eligible_offers[0]

        return PortfolioCustomerRow(
            customer_id=analysis.customer_id,
            full_name=analysis.customer_name,
            segment=analysis.customer_segment,
            relationship_start_date=customer.relationship_start_date,
            churn_score=analysis.churn_result.score,
            value_score=analysis.value_result.score,
            priority_score=analysis.priority_result.priority_score,
            decision=analysis.priority_result.decision,
            primary_trigger=analysis.primary_trigger,
            recommended_action=analysis.suggested_action,
            top_eligible_offer_id=top_eligible.offer_id if top_eligible else None,
            top_eligible_offer_name=top_eligible.offer_name if top_eligible else None,
            revenue_at_risk=_revenue_at_risk(analysis, customer.estimated_annual_value),
            expected_net_benefit=(
                top_financial.financials.expected_net_benefit if top_financial else None
            ),
            recommendation_status=saved.status.value if saved else None,
            has_data_warning=bool(analysis.customer_360_warnings),
            last_analyzed_at=analysis.generated_at,
        )
