"""Recommendation persistence from validated flow outputs."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Session, select

from app.core.config import Settings, get_settings
from app.core.policy_rules import POLICY_VERSION
from app.core.scoring_rules import ANALYSIS_VERSION
from app.models.enums import CreatedByMode, RecommendationDecision, RecommendationStatus
from app.models.recommendation import Recommendation
from app.schemas.analysis import RulesOnlyAnalysisResponse
from app.schemas.crew_result import RetentionCrewResult


def _utc_now() -> datetime:
    return datetime.now(UTC)


class RecommendationService:
    """Persist validated retention recommendations."""

    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self.session = session
        self.settings = settings or get_settings()

    def get_recommendation_for_event(self, event_id: str) -> Recommendation | None:
        """Return the latest recommendation linked to an event."""
        statement = (
            select(Recommendation)
            .where(Recommendation.triggering_event_id == event_id)
            .order_by(Recommendation.created_at.desc())
        )
        return self.session.exec(statement).first()

    def has_completed_recommendation_for_event(self, event_id: str) -> bool:
        """Return True when a recommendation already exists for an event."""
        return self.get_recommendation_for_event(event_id) is not None

    def create_from_rules_analysis(
        self,
        *,
        analysis: RulesOnlyAnalysisResponse,
        execution_id: str,
        event_id: str | None = None,
        created_by_mode: CreatedByMode = CreatedByMode.RULES_ONLY,
        investigation_summary: str | None = None,
        policy_warnings: list[str] | None = None,
        validation_warnings: list[str] | None = None,
    ) -> Recommendation:
        """Persist a rules-only or monitor recommendation."""
        if event_id and self.has_completed_recommendation_for_event(event_id):
            existing = self.get_recommendation_for_event(event_id)
            if existing is not None:
                return existing

        top_financial = analysis.financial_options[0] if analysis.financial_options else None
        recommended_offer_id = top_financial.offer_id if top_financial else None
        alternate_offer_id = None
        if len(analysis.financial_options) > 1:
            alternate_offer_id = analysis.financial_options[1].offer_id

        revenue_at_risk = 0.0
        expected_net = 0.0
        if top_financial:
            revenue_at_risk = top_financial.financials.revenue_at_risk
            expected_net = top_financial.financials.expected_net_benefit

        recommendation = Recommendation(
            customer_id=analysis.customer_id,
            triggering_event_id=event_id,
            analysis_execution_id=execution_id,
            churn_score=float(analysis.churn_result.score),
            value_score=float(analysis.value_result.score),
            priority_score=float(analysis.priority_result.priority_score),
            decision=analysis.priority_result.decision,
            recommended_offer_id=recommended_offer_id,
            alternate_offer_id=alternate_offer_id,
            revenue_at_risk=revenue_at_risk,
            expected_net_benefit=expected_net,
            confidence=0.75,
            summary=analysis.suggested_action,
            investigation_summary=investigation_summary or analysis.suggested_action,
            created_by_mode=created_by_mode,
            calculation_version=ANALYSIS_VERSION,
            policy_version=POLICY_VERSION,
            evidence_json={"primary_trigger": analysis.primary_trigger},
            rm_brief_json={},
            policy_warnings_json=list(
                policy_warnings or analysis.eligibility_result.policy_warnings
            ),
            validation_warnings_json=list(validation_warnings or []),
            status=RecommendationStatus.NEW,
        )
        self.session.add(recommendation)
        self.session.flush()
        return recommendation

    def create_from_crew_result(
        self,
        *,
        analysis: RulesOnlyAnalysisResponse,
        crew_result: RetentionCrewResult,
        execution_id: str,
        event_id: str | None = None,
        validation_warnings: list[str] | None = None,
    ) -> Recommendation:
        """Persist an agentic recommendation from validated crew output."""
        if event_id and self.has_completed_recommendation_for_event(event_id):
            existing = self.get_recommendation_for_event(event_id)
            if existing is not None:
                return existing

        offer = crew_result.offer_strategy
        revenue_at_risk = 0.0
        expected_net = offer.expected_net_benefit or 0.0
        if offer.recommended_offer_id:
            financial = next(
                (
                    opt
                    for opt in analysis.financial_options
                    if opt.offer_id == offer.recommended_offer_id
                ),
                None,
            )
            if financial:
                revenue_at_risk = financial.financials.revenue_at_risk
                if offer.expected_net_benefit is None:
                    expected_net = financial.financials.expected_net_benefit

        mode = CreatedByMode.MOCK if self.settings.mock_llm_mode else CreatedByMode.QWEN
        recommendation = Recommendation(
            customer_id=analysis.customer_id,
            triggering_event_id=event_id,
            analysis_execution_id=execution_id,
            churn_score=float(analysis.churn_result.score),
            value_score=float(analysis.value_result.score),
            priority_score=float(analysis.priority_result.priority_score),
            decision=analysis.priority_result.decision,
            recommended_offer_id=offer.recommended_offer_id,
            alternate_offer_id=offer.alternate_offer_id,
            revenue_at_risk=revenue_at_risk,
            expected_net_benefit=expected_net,
            confidence=crew_result.rm_brief.confidence,
            summary=crew_result.rm_brief.executive_summary,
            investigation_summary=crew_result.investigation.investigation_summary,
            created_by_mode=mode,
            calculation_version=ANALYSIS_VERSION,
            policy_version=POLICY_VERSION,
            evidence_json={
                "evidence_references": [
                    ref.model_dump(mode="json") for ref in crew_result.rm_brief.evidence_references
                ],
                "talking_points": crew_result.rm_brief.talking_points,
            },
            rm_brief_json=crew_result.rm_brief.model_dump(mode="json"),
            policy_warnings_json=list(offer.policy_warnings),
            validation_warnings_json=list(validation_warnings or []),
            status=RecommendationStatus.NEW,
        )
        self.session.add(recommendation)
        self.session.flush()
        return recommendation

    def should_persist_no_action(self, decision: RecommendationDecision) -> bool:
        if decision != RecommendationDecision.NO_ACTION:
            return True
        return self.settings.persist_no_action_recommendations
