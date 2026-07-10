"""Safe read-only chat tools for RM copilot."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import Field
from sqlmodel import Session, select

from app.core.agent_policy import AGENT_ELIGIBILITY_DISCLAIMER
from app.core.exceptions import ResourceNotFoundError
from app.models.bureau_trigger import BureauTrigger
from app.models.customer import Customer
from app.models.enums import FreshnessStatus, RecommendationDecision
from app.schemas.analysis import RulesOnlyAnalysisResponse
from app.schemas.chat import VALID_CUSTOMER_IDS, ChatEvidence
from app.schemas.common import APIModel
from app.services.analysis_service import AnalysisService
from app.services.customer_360_service import Customer360Service
from app.services.customer_repository import CustomerRepository
from app.services.portfolio_service import PortfolioService
from app.services.recommendation_repository import RecommendationRepository

ALLOWED_CHAT_TOOLS: frozenset[str] = frozenset(
    {
        "get_chat_customer_summary",
        "get_chat_customer_risk_explanation",
        "get_chat_customer_eligibility",
        "get_chat_customer_recommendation",
        "get_chat_priority_customers",
        "get_chat_portfolio_summary",
        "search_customers_by_trigger",
        "compare_customers",
        "get_customer_data_freshness",
        "get_customers_with_stale_data",
        "get_rm_talking_points",
        "get_recommendation_status",
    }
)

TRIGGER_SEARCH_MAP: dict[str, set[str]] = {
    "HOME_LOAN": {"HOME_LOAN", "EXTERNAL_HOME_LOAN_INQUIRY"},
    "CREDIT_CARD": {"CREDIT_CARD", "EXTERNAL_CARD_INQUIRY"},
    "SALARY_STOPPED": {"SALARY_STOPPED", "SALARY_CREDIT_STOPPED"},
    "FIXED_DEPOSIT": {"FIXED_DEPOSIT", "FIXED_DEPOSIT_MATURITY"},
    "TRAVEL": {"TRAVEL", "TRAVEL_CARD"},
    "FOREX": {"FOREX", "FOREX_SPEND"},
    "EXTERNAL_TRANSFER": {"EXTERNAL_TRANSFER", "LARGE_EXTERNAL_TRANSFER"},
    "INVESTMENT": {"INVESTMENT", "INVESTMENT_TRANSFER"},
}


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _normalize_customer_id(customer_id: str) -> str:
    normalized = customer_id.strip().upper()
    if normalized not in VALID_CUSTOMER_IDS:
        raise ResourceNotFoundError(
            code="CUSTOMER_NOT_FOUND",
            message=f"Customer {normalized} was not found",
        )
    return normalized


def _validate_customer_ids(customer_ids: list[str]) -> list[str]:
    if not 2 <= len(customer_ids) <= 5:
        raise ValueError("Comparison requires between 2 and 5 customer IDs")
    return [_normalize_customer_id(customer_id) for customer_id in customer_ids]


def _analyze(session: Session, customer_id: str) -> RulesOnlyAnalysisResponse:
    return AnalysisService(session).analyze_customer_rules_only(customer_id)


def _format_inr(amount: float) -> str:
    return f"INR {amount:,.2f}"


class ChatCustomerSummary(APIModel):
    customer_id: str
    full_name: str
    segment: str
    churn_score: int
    value_score: int
    priority_score: int
    decision: str
    primary_trigger: str | None
    suggested_action: str
    latest_recommendation_status: str | None
    recommended_offer_name: str | None
    data_warnings: list[str] = Field(default_factory=list)


class ChatRiskExplanation(APIModel):
    customer_id: str
    churn_score: int
    value_score: int
    priority_score: int
    decision: str
    triggered_rules: list[str]
    primary_signal: str | None
    counter_signals: list[str] = Field(default_factory=list)
    top_risk_signals: list[str] = Field(default_factory=list)


class ChatEligibilitySummary(APIModel):
    customer_id: str
    eligible_offers: list[dict[str, Any]]
    rejected_offers: list[dict[str, Any]]
    policy_warnings: list[str]
    approval_disclaimer: str = AGENT_ELIGIBILITY_DISCLAIMER


class ChatRecommendationSummary(APIModel):
    customer_id: str
    has_recommendation: bool
    recommendation_id: str | None = None
    status: str | None = None
    decision: str | None = None
    recommended_offer_id: str | None = None
    recommended_offer_name: str | None = None
    revenue_at_risk: float | None = None
    expected_net_benefit: float | None = None
    executive_summary: str | None = None
    talking_points: list[str] = Field(default_factory=list)
    evidence_references: list[dict[str, Any]] = Field(default_factory=list)


class ChatPriorityCustomer(APIModel):
    customer_id: str
    full_name: str
    priority_score: int
    decision: str
    primary_trigger: str | None
    suggested_action: str
    revenue_at_risk: float


class ChatPortfolioChatSummary(APIModel):
    total_customers: int
    retain_count: int
    review_count: int
    monitor_count: int
    no_action_count: int
    total_revenue_at_risk: float
    total_positive_expected_net_benefit: float
    open_alerts: int
    high_value_high_risk_count: int


class ChatTriggerMatch(APIModel):
    customer_id: str
    trigger_type: str
    severity: str
    trigger_date: str | None
    decision: str
    priority_score: int


class ChatCustomerComparison(APIModel):
    customer_id: str
    full_name: str
    churn_score: int
    value_score: int
    priority_score: int
    decision: str
    primary_trigger: str | None
    revenue_at_risk: float
    top_offer_name: str | None
    data_warnings: list[str] = Field(default_factory=list)


class ChatDataFreshness(APIModel):
    customer_id: str
    sources: dict[str, str]
    stale_sources: list[str]
    data_warnings: list[str]


class ChatStaleCustomer(APIModel):
    customer_id: str
    full_name: str
    stale_sources: list[str]


class ChatTalkingPoints(APIModel):
    customer_id: str
    executive_summary: str
    talking_points: list[str]
    recommended_action: str
    eligibility_disclaimer: str = AGENT_ELIGIBILITY_DISCLAIMER


def get_chat_customer_summary(session: Session, customer_id: str) -> ChatCustomerSummary:
    """Return concise customer summary for chat."""
    normalized = _normalize_customer_id(customer_id)
    analysis = _analyze(session, normalized)
    saved = RecommendationRepository(session).list_all_by_customer(normalized)
    top_offer = None
    if analysis.financial_options:
        top_offer = analysis.financial_options[0].offer_name
    elif analysis.eligibility_result.eligible_offers:
        top_offer = analysis.eligibility_result.eligible_offers[0].offer_name
    return ChatCustomerSummary(
        customer_id=normalized,
        full_name=analysis.customer_name,
        segment=analysis.customer_segment.value,
        churn_score=analysis.churn_result.score,
        value_score=analysis.value_result.score,
        priority_score=analysis.priority_result.priority_score,
        decision=analysis.priority_result.decision.value,
        primary_trigger=analysis.primary_trigger,
        suggested_action=analysis.suggested_action,
        latest_recommendation_status=saved[0].status.value if saved else None,
        recommended_offer_name=top_offer,
        data_warnings=list(analysis.customer_360_warnings),
    )


def get_chat_customer_risk_explanation(
    session: Session, customer_id: str
) -> ChatRiskExplanation:
    """Return risk explanation with rule contributions."""
    normalized = _normalize_customer_id(customer_id)
    analysis = _analyze(session, normalized)
    triggered = [
        c.description
        for c in analysis.churn_result.contributions
        if c.triggered
    ]
    counter = [
        c.description
        for c in analysis.churn_result.contributions
        if not c.triggered and c.points > 0
    ][:3]
    return ChatRiskExplanation(
        customer_id=normalized,
        churn_score=analysis.churn_result.score,
        value_score=analysis.value_result.score,
        priority_score=analysis.priority_result.priority_score,
        decision=analysis.priority_result.decision.value,
        triggered_rules=triggered,
        primary_signal=analysis.primary_trigger,
        counter_signals=counter,
        top_risk_signals=list(analysis.top_risk_signals),
    )


def get_chat_customer_eligibility(session: Session, customer_id: str) -> ChatEligibilitySummary:
    """Return eligibility and rejection reasons."""
    normalized = _normalize_customer_id(customer_id)
    analysis = _analyze(session, normalized)
    eligible = [
        {
            "offer_id": offer.offer_id,
            "offer_name": offer.offer_name,
            "product_type": offer.product_type,
        }
        for offer in analysis.eligibility_result.eligible_offers
    ]
    rejected = [
        {
            "offer_id": offer.offer_id,
            "offer_name": offer.offer_name,
            "reason_codes": list(offer.reason_codes),
        }
        for offer in analysis.eligibility_result.rejected_offers
    ]
    return ChatEligibilitySummary(
        customer_id=normalized,
        eligible_offers=eligible,
        rejected_offers=rejected,
        policy_warnings=list(analysis.eligibility_result.policy_warnings),
    )


def get_chat_customer_recommendation(
    session: Session, customer_id: str
) -> ChatRecommendationSummary:
    """Return latest recommendation details."""
    normalized = _normalize_customer_id(customer_id)
    analysis = _analyze(session, normalized)
    try:
        detail = RecommendationRepository(session).get_latest_by_customer(normalized)
    except ResourceNotFoundError:
        return ChatRecommendationSummary(
            customer_id=normalized,
            has_recommendation=False,
            executive_summary=analysis.suggested_action,
        )
    talking_points: list[str] = []
    evidence_refs: list[dict[str, Any]] = []
    if detail.evidence_json:
        talking_points = list(detail.evidence_json.get("talking_points") or [])
        evidence_refs = list(detail.evidence_json.get("evidence_references") or [])
    offer_name = None
    if detail.recommended_offer_id and analysis.financial_options:
        for opt in analysis.financial_options:
            if opt.offer_id == detail.recommended_offer_id:
                offer_name = opt.offer_name
                break
    return ChatRecommendationSummary(
        customer_id=normalized,
        has_recommendation=True,
        recommendation_id=detail.recommendation_id,
        status=detail.status.value,
        decision=detail.decision.value,
        recommended_offer_id=detail.recommended_offer_id,
        recommended_offer_name=offer_name,
        revenue_at_risk=detail.revenue_at_risk,
        expected_net_benefit=detail.expected_net_benefit,
        executive_summary=detail.summary,
        talking_points=talking_points,
        evidence_references=evidence_refs,
    )


def get_chat_priority_customers(session: Session, *, limit: int = 10) -> list[ChatPriorityCustomer]:
    """Return highest-priority customers excluding NO_ACTION as urgent."""
    bounded = max(1, min(limit, 20))
    page = PortfolioService(session).list_customers(
        page=1,
        page_size=bounded,
        sort_by="priority_score",
        sort_order="desc",
    )
    results: list[ChatPriorityCustomer] = []
    for row in page.items:
        if row.decision == RecommendationDecision.NO_ACTION:
            continue
        results.append(
            ChatPriorityCustomer(
                customer_id=row.customer_id,
                full_name=row.full_name,
                priority_score=row.priority_score,
                decision=row.decision.value,
                primary_trigger=row.primary_trigger,
                suggested_action=row.recommended_action,
                revenue_at_risk=row.revenue_at_risk,
            )
        )
    return results[:bounded]


def get_chat_portfolio_summary(session: Session) -> ChatPortfolioChatSummary:
    """Return portfolio summary for chat."""
    summary = PortfolioService(session).get_summary()
    return ChatPortfolioChatSummary(
        total_customers=summary.total_customers,
        retain_count=summary.immediate_intervention_count,
        review_count=summary.review_count,
        monitor_count=summary.monitor_count,
        no_action_count=summary.no_action_count,
        total_revenue_at_risk=summary.total_revenue_at_risk,
        total_positive_expected_net_benefit=summary.total_positive_expected_net_benefit,
        open_alerts=summary.open_alerts,
        high_value_high_risk_count=summary.high_value_high_risk_count,
    )


def search_customers_by_trigger(
    session: Session, trigger_type: str
) -> list[ChatTriggerMatch]:
    """Search customers by bureau trigger type."""
    normalized_type = trigger_type.strip().upper()
    search_tokens = TRIGGER_SEARCH_MAP.get(normalized_type, {normalized_type})
    triggers = session.exec(select(BureauTrigger)).all()
    matches: list[ChatTriggerMatch] = []
    seen: set[str] = set()
    for trigger in triggers:
        product = trigger.product_type.upper()
        trigger_name = trigger.trigger_type.upper()
        if not (
            normalized_type in product
            or normalized_type in trigger_name
            or product in search_tokens
            or trigger_name in search_tokens
            or any(token in product or token in trigger_name for token in search_tokens)
        ):
            continue
        if trigger.customer_id in seen:
            continue
        seen.add(trigger.customer_id)
        analysis = _analyze(session, trigger.customer_id)
        matches.append(
            ChatTriggerMatch(
                customer_id=trigger.customer_id,
                trigger_type=trigger.product_type,
                severity=trigger.severity.value,
                trigger_date=trigger.trigger_date.isoformat() if trigger.trigger_date else None,
                decision=analysis.priority_result.decision.value,
                priority_score=analysis.priority_result.priority_score,
            )
        )
    if normalized_type in {"SALARY_STOPPED", "SALARY_CREDIT_STOPPED"}:
        customers = session.exec(select(Customer)).all()
        for customer in customers:
            if customer.customer_id in seen:
                continue
            analysis = _analyze(session, customer.customer_id)
            c360 = Customer360Service(session).get_customer_360(customer.customer_id)
            features = c360.transaction_features
            if features and features.salary_received_current_month is False:
                matches.append(
                    ChatTriggerMatch(
                        customer_id=customer.customer_id,
                        trigger_type="SALARY_STOPPED",
                        severity="HIGH",
                        trigger_date=None,
                        decision=analysis.priority_result.decision.value,
                        priority_score=analysis.priority_result.priority_score,
                    )
                )
    matches.sort(key=lambda item: item.priority_score, reverse=True)
    return matches


def compare_customers(
    session: Session, customer_ids: list[str]
) -> list[ChatCustomerComparison]:
    """Compare 2 to 5 customers on key retention metrics."""
    normalized_ids = _validate_customer_ids(customer_ids)
    comparisons: list[ChatCustomerComparison] = []
    for customer_id in normalized_ids:
        analysis = _analyze(session, customer_id)
        top_offer = None
        if analysis.financial_options:
            top_offer = analysis.financial_options[0].offer_name
        revenue = 0.0
        if analysis.financial_options:
            revenue = analysis.financial_options[0].financials.revenue_at_risk
        customer = CustomerRepository(session).get_by_id(customer_id)
        comparisons.append(
            ChatCustomerComparison(
                customer_id=customer_id,
                full_name=customer.full_name,
                churn_score=analysis.churn_result.score,
                value_score=analysis.value_result.score,
                priority_score=analysis.priority_result.priority_score,
                decision=analysis.priority_result.decision.value,
                primary_trigger=analysis.primary_trigger,
                revenue_at_risk=revenue,
                top_offer_name=top_offer,
                data_warnings=list(analysis.customer_360_warnings),
            )
        )
    return comparisons


def get_customer_data_freshness(session: Session, customer_id: str) -> ChatDataFreshness:
    """Return data freshness for a customer."""
    normalized = _normalize_customer_id(customer_id)
    c360 = Customer360Service(session).get_customer_360(normalized)
    sources = {
        "core_banking": c360.data_freshness.core_banking.status.value,
        "credit_history": c360.data_freshness.credit_history.status.value,
        "bureau_triggers": c360.data_freshness.bureau_triggers.status.value,
        "transaction_history": c360.data_freshness.transaction_history.status.value,
    }
    stale = [name for name, status in sources.items() if status == FreshnessStatus.STALE.value]
    missing = [name for name, status in sources.items() if status == FreshnessStatus.MISSING.value]
    return ChatDataFreshness(
        customer_id=normalized,
        sources=sources,
        stale_sources=stale + missing,
        data_warnings=list(c360.data_warnings),
    )


def get_customers_with_stale_data(
    session: Session, *, limit: int = 20
) -> list[ChatStaleCustomer]:
    """Return customers with stale or missing data sources."""
    bounded = max(1, min(limit, 50))
    customers = session.exec(select(Customer)).all()
    stale_customers: list[ChatStaleCustomer] = []
    for customer in customers:
        freshness = get_customer_data_freshness(session, customer.customer_id)
        if freshness.stale_sources:
            stale_customers.append(
                ChatStaleCustomer(
                    customer_id=customer.customer_id,
                    full_name=customer.full_name,
                    stale_sources=freshness.stale_sources,
                )
            )
        if len(stale_customers) >= bounded:
            break
    return stale_customers


def get_rm_talking_points(session: Session, customer_id: str) -> ChatTalkingPoints:
    """Return RM talking points from latest recommendation or analysis."""
    normalized = _normalize_customer_id(customer_id)
    analysis = _analyze(session, normalized)
    try:
        detail = RecommendationRepository(session).get_latest_by_customer(normalized)
        points = list(detail.evidence_json.get("talking_points") or [])
        if detail.rm_brief_json:
            points = list(detail.rm_brief_json.get("talking_points") or points)
        return ChatTalkingPoints(
            customer_id=normalized,
            executive_summary=detail.summary,
            talking_points=points or [analysis.suggested_action],
            recommended_action=analysis.suggested_action,
        )
    except ResourceNotFoundError:
        signals = ", ".join(analysis.top_risk_signals[:3]) or "routine monitoring"
        return ChatTalkingPoints(
            customer_id=normalized,
            executive_summary=f"Review {analysis.customer_name} based on {signals}.",
            talking_points=[
                f"Priority score is {analysis.priority_result.priority_score}.",
                f"Suggested action: {analysis.suggested_action}",
                AGENT_ELIGIBILITY_DISCLAIMER,
            ],
            recommended_action=analysis.suggested_action,
        )


def get_recommendation_status(session: Session, customer_id: str) -> ChatRecommendationSummary:
    """Return recommendation workflow status."""
    return get_chat_customer_recommendation(session, customer_id)


def build_evidence_from_tool(
    tool_name: str, payload: Any, *, customer_id: str | None = None
) -> list[ChatEvidence]:
    """Build safe evidence references from tool output."""
    evidence: list[ChatEvidence] = []
    if tool_name == "get_chat_customer_risk_explanation" and hasattr(payload, "primary_signal"):
        if payload.primary_signal:
            evidence.append(
                ChatEvidence(
                    source_system="TRANSACTION_ENGINE",
                    source_type="risk_signal",
                    customer_id=payload.customer_id,
                    field="primary_signal",
                    value_summary=payload.primary_signal,
                )
            )
        evidence.append(
            ChatEvidence(
                source_system="CORE_BANKING",
                source_type="priority_score",
                customer_id=payload.customer_id,
                field="priority_score",
                value_summary=str(payload.priority_score),
            )
        )
    elif tool_name == "get_chat_portfolio_summary":
        evidence.append(
            ChatEvidence(
                source_system="CRM",
                source_type="portfolio_summary",
                field="total_revenue_at_risk",
                value_summary=_format_inr(payload.total_revenue_at_risk),
            )
        )
    elif tool_name == "get_chat_customer_eligibility" and customer_id:
        if payload.rejected_offers:
            first = payload.rejected_offers[0]
            evidence.append(
                ChatEvidence(
                    source_system="CORE_BANKING",
                    source_type="eligibility",
                    customer_id=customer_id,
                    field="rejected_offer",
                    value_summary=(
                        f"{first.get('offer_name')} "
                        f"({', '.join(first.get('reason_codes', []))})"
                    ),
                )
            )
    elif tool_name == "get_chat_customer_recommendation" and hasattr(payload, "customer_id"):
        if payload.has_recommendation:
            evidence.append(
                ChatEvidence(
                    source_system="CRM",
                    source_type="recommendation",
                    customer_id=payload.customer_id,
                    field="recommended_offer",
                    value_summary=payload.recommended_offer_name or payload.recommended_offer_id,
                )
            )
    elif tool_name == "get_chat_customer_summary" and hasattr(payload, "customer_id"):
        if payload.recommended_offer_name:
            evidence.append(
                ChatEvidence(
                    source_system="CORE_BANKING",
                    source_type="offer_summary",
                    customer_id=payload.customer_id,
                    field="recommended_offer",
                    value_summary=payload.recommended_offer_name,
                )
            )
    elif tool_name == "compare_customers":
        for row in payload:
            evidence.append(
                ChatEvidence(
                    source_system="CORE_BANKING",
                    source_type="comparison",
                    customer_id=row.customer_id,
                    field="priority_score",
                    value_summary=str(row.priority_score),
                )
            )
    return evidence
