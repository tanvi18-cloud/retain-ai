"""Rules-only customer analysis orchestration."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Session

from app.core.scoring_rules import ANALYSIS_VERSION
from app.models.enums import RecommendationDecision
from app.schemas.analysis import OfferFinancialOption, RulesOnlyAnalysisResponse
from app.schemas.customer_360 import Customer360Response
from app.schemas.eligibility import EligibleOffer
from app.schemas.scoring import ScoreResult
from app.services.customer_360_service import Customer360Service
from app.services.eligibility_service import EligibilityService
from app.services.financial_value_service import FinancialValueService
from app.services.offer_repository import OfferRepository
from app.services.scoring_service import ScoringService

_TRIGGER_PRODUCT_MAP = {
    "HOME_LOAN": {"HOME_LOAN"},
    "CREDIT_CARD": {"CREDIT_CARD"},
    "TRAVEL_CARD": {"TRAVEL_CARD", "CREDIT_CARD"},
    "FIXED_DEPOSIT": {"FIXED_DEPOSIT"},
    "WEALTH_MANAGEMENT": {"RELATIONSHIP"},
    "INVESTMENT": {"RELATIONSHIP"},
    "PERSONAL_LOAN": {"RELATIONSHIP", "REPAYMENT"},
}


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _primary_trigger(churn_result: ScoreResult) -> str | None:
    triggered = [c for c in churn_result.contributions if c.triggered]
    if not triggered:
        return None
    top = max(triggered, key=lambda c: c.points)
    return top.rule_code


def _top_risk_signals(churn_result: ScoreResult) -> list[str]:
    triggered = [c for c in churn_result.contributions if c.triggered]
    sorted_rules = sorted(triggered, key=lambda c: c.points, reverse=True)
    return [rule.description for rule in sorted_rules[:5]]


def _scenario_relevance(
    offer: EligibleOffer,
    customer_360: Customer360Response,
) -> int:
    """Return a deterministic scenario relevance score for ranking."""
    score = 0
    trigger_products = {trigger.product_type for trigger in customer_360.bureau_triggers}
    for trigger_product in trigger_products:
        mapped = _TRIGGER_PRODUCT_MAP.get(trigger_product, set())
        if offer.product_type in mapped:
            score += 3
    if offer.product_type == "FIXED_DEPOSIT" and any(
        account.fixed_deposit_maturity_date is not None for account in customer_360.accounts
    ):
        score += 2
    return score


def _suggested_action(
    *,
    decision: RecommendationDecision,
    top_offer: EligibleOffer | None,
    primary_trigger: str | None,
) -> str:
    if decision == RecommendationDecision.NO_ACTION:
        return "No immediate retention action required; continue routine monitoring."
    if top_offer is None:
        if decision == RecommendationDecision.RETAIN:
            return "Schedule RM retention review based on elevated churn risk signals."
        if decision == RecommendationDecision.REVIEW:
            return "Review customer relationship and assess retention options."
        return "Monitor customer activity and reassess if risk signals increase."
    action_prefix = {
        RecommendationDecision.RETAIN: "Prioritize retention discussion:",
        RecommendationDecision.REVIEW: "Review retention option:",
        RecommendationDecision.MONITOR: "Monitor and consider:",
    }.get(decision, "Consider:")
    trigger_note = f" Primary signal: {primary_trigger}." if primary_trigger else ""
    return f"{action_prefix} {top_offer.offer_name}.{trigger_note}"


class AnalysisService:
    """Orchestrate deterministic rules-only customer analysis."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.customer_360_service = Customer360Service(session)
        self.scoring_service = ScoringService()
        self.eligibility_service = EligibilityService()
        self.financial_service = FinancialValueService()
        self.offer_repository = OfferRepository(session)

    def analyze_customer_rules_only(self, customer_id: str) -> RulesOnlyAnalysisResponse:
        """Run synchronous rules-only analysis without persisting recommendations."""
        customer_360 = self.customer_360_service.get_customer_360(customer_id)
        churn_result = self.scoring_service.calculate_churn_risk(customer_360)
        value_result = self.scoring_service.calculate_customer_value(customer_360)
        priority_result = self.scoring_service.calculate_priority(
            churn_result=churn_result,
            value_result=value_result,
        )

        active_offers = self.offer_repository.list_all_active()
        eligibility_result = self.eligibility_service.evaluate_offers(
            customer_360,
            active_offers,
            value_result=value_result,
        )

        eligible_by_id = {offer.offer_id: offer for offer in eligibility_result.eligible_offers}
        financial_options: list[OfferFinancialOption] = []
        for eligible_offer in eligibility_result.eligible_offers:
            financials = self.financial_service.calculate_retention_financials(
                annual_customer_value=customer_360.customer.estimated_annual_value,
                churn_score=churn_result.score,
                expected_retention_uplift=eligible_offer.expected_retention_uplift,
                estimated_offer_cost=eligible_offer.estimated_cost,
            )
            financial_options.append(
                OfferFinancialOption(
                    offer_id=eligible_offer.offer_id,
                    offer_name=eligible_offer.offer_name,
                    product_type=eligible_offer.product_type,
                    financials=financials,
                )
            )

        financial_options.sort(
            key=lambda option: (
                option.financials.expected_net_benefit,
                _scenario_relevance(eligible_by_id[option.offer_id], customer_360),
            ),
            reverse=True,
        )

        primary = _primary_trigger(churn_result)
        top_offer = None
        if financial_options:
            top_offer = eligible_by_id.get(financial_options[0].offer_id)
        elif eligibility_result.eligible_offers:
            top_offer = eligibility_result.eligible_offers[0]

        return RulesOnlyAnalysisResponse(
            customer_id=customer_360.customer.customer_id,
            customer_name=customer_360.customer.full_name,
            customer_segment=customer_360.customer.segment,
            customer_360_warnings=customer_360.data_warnings,
            churn_result=churn_result,
            value_result=value_result,
            priority_result=priority_result,
            eligibility_result=eligibility_result,
            financial_options=financial_options,
            top_risk_signals=_top_risk_signals(churn_result),
            primary_trigger=primary,
            suggested_action=_suggested_action(
                decision=priority_result.decision,
                top_offer=top_offer,
                primary_trigger=primary,
            ),
            generated_at=_utc_now(),
            analysis_version=ANALYSIS_VERSION,
        )
