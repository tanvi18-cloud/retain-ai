"""Recommendation persistence operations."""

from sqlmodel import Session, select

from app.core.exceptions import ResourceNotFoundError
from app.models.enums import RecommendationDecision, RecommendationStatus
from app.models.recommendation import Recommendation
from app.schemas.common import PaginatedResponse
from app.schemas.recommendations import RecommendationDetail, RecommendationSummary
from app.services.repository_utils import count_query, paginate_offset, validate_pagination


def _to_summary(recommendation: Recommendation) -> RecommendationSummary:
    return RecommendationSummary(
        recommendation_id=recommendation.id,
        customer_id=recommendation.customer_id,
        churn_score=recommendation.churn_score,
        value_score=recommendation.value_score,
        priority_score=recommendation.priority_score,
        decision=recommendation.decision,
        status=recommendation.status,
        recommended_offer_id=recommendation.recommended_offer_id,
    )


def _to_detail(recommendation: Recommendation) -> RecommendationDetail:
    return RecommendationDetail(
        recommendation_id=recommendation.id,
        customer_id=recommendation.customer_id,
        triggering_event_id=recommendation.triggering_event_id,
        churn_score=recommendation.churn_score,
        value_score=recommendation.value_score,
        priority_score=recommendation.priority_score,
        decision=recommendation.decision,
        recommended_offer_id=recommendation.recommended_offer_id,
        alternate_offer_id=recommendation.alternate_offer_id,
        revenue_at_risk=recommendation.revenue_at_risk,
        expected_net_benefit=recommendation.expected_net_benefit,
        confidence=recommendation.confidence,
        summary=recommendation.summary,
        evidence_json=recommendation.evidence_json,
        status=recommendation.status,
        created_at=recommendation.created_at,
        updated_at=recommendation.updated_at,
    )


class RecommendationRepository:
    """Data access for retention recommendations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, recommendation_id: str) -> RecommendationDetail:
        """Return a recommendation by ID or raise when not found."""
        recommendation = self.session.get(Recommendation, recommendation_id)
        if recommendation is None:
            raise ResourceNotFoundError(
                code="RECOMMENDATION_NOT_FOUND",
                message=f"Recommendation {recommendation_id} was not found",
            )
        return _to_detail(recommendation)

    def list_by_customer(
        self,
        customer_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[RecommendationSummary]:
        """Return recommendations for a customer ordered by newest first."""
        validate_pagination(page, page_size)
        statement = (
            select(Recommendation)
            .where(Recommendation.customer_id == customer_id)
            .order_by(Recommendation.created_at.desc())
        )
        total = count_query(self.session, statement)
        recommendations = self.session.exec(
            statement.offset(paginate_offset(page, page_size)).limit(page_size)
        ).all()
        return PaginatedResponse.build(
            items=[_to_summary(item) for item in recommendations],
            total=total,
            page=page,
            page_size=page_size,
        )

    def list_all_by_customer(self, customer_id: str) -> list[RecommendationSummary]:
        """Return all recommendations for a customer ordered newest first."""
        statement = (
            select(Recommendation)
            .where(Recommendation.customer_id == customer_id)
            .order_by(Recommendation.created_at.desc())
        )
        recommendations = self.session.exec(statement).all()
        return [_to_summary(item) for item in recommendations]

    def get_latest_by_customer(self, customer_id: str) -> RecommendationDetail:
        """Return the most recent recommendation for a customer."""
        statement = (
            select(Recommendation)
            .where(Recommendation.customer_id == customer_id)
            .order_by(Recommendation.created_at.desc())
            .limit(1)
        )
        recommendation = self.session.exec(statement).first()
        if recommendation is None:
            raise ResourceNotFoundError(
                code="RECOMMENDATION_NOT_FOUND",
                message=f"No recommendation found for customer {customer_id}",
                details={"customer_id": customer_id},
            )
        return _to_detail(recommendation)

    def list_recommendations(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        status: RecommendationStatus | None = None,
        decision: RecommendationDecision | None = None,
    ) -> PaginatedResponse[RecommendationSummary]:
        """Return paginated recommendations with optional filters."""
        validate_pagination(page, page_size)
        statement = select(Recommendation).order_by(Recommendation.priority_score.desc())
        if status is not None:
            statement = statement.where(Recommendation.status == status)
        if decision is not None:
            statement = statement.where(Recommendation.decision == decision)
        total = count_query(self.session, statement)
        recommendations = self.session.exec(
            statement.offset(paginate_offset(page, page_size)).limit(page_size)
        ).all()
        return PaginatedResponse.build(
            items=[_to_summary(item) for item in recommendations],
            total=total,
            page=page,
            page_size=page_size,
        )
