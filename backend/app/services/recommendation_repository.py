"""Recommendation persistence operations."""

from typing import Literal

from sqlmodel import Session, select

from app.core.exceptions import ResourceNotFoundError, UnsupportedSortFieldError
from app.models.enums import RecommendationDecision, RecommendationStatus
from app.models.recommendation import Recommendation
from app.schemas.common import PaginatedResponse
from app.schemas.recommendations import RecommendationDetail, RecommendationSummary
from app.services.repository_utils import count_query, paginate_offset, validate_pagination

RecommendationSortField = Literal["created_at", "priority_score"]
SortOrder = Literal["asc", "desc"]


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


def _to_detail(recommendation: Recommendation, interactions=None) -> RecommendationDetail:
    return RecommendationDetail(
        recommendation_id=recommendation.id,
        customer_id=recommendation.customer_id,
        triggering_event_id=recommendation.triggering_event_id,
        analysis_execution_id=recommendation.analysis_execution_id,
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
        investigation_summary=recommendation.investigation_summary,
        evidence_json=recommendation.evidence_json,
        rm_brief_json=recommendation.rm_brief_json or {},
        policy_warnings_json=list(recommendation.policy_warnings_json or []),
        validation_warnings_json=list(recommendation.validation_warnings_json or []),
        created_by_mode=recommendation.created_by_mode,
        calculation_version=recommendation.calculation_version,
        policy_version=recommendation.policy_version,
        status=recommendation.status,
        created_at=recommendation.created_at,
        updated_at=recommendation.updated_at,
        interactions=interactions or [],
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
        from app.services.interaction_repository import InteractionRepository

        interactions = InteractionRepository(self.session).list_recent_by_customer(
            recommendation.customer_id,
            limit=10,
        )
        return _to_detail(recommendation, interactions=interactions)

    def get_model_by_id(self, recommendation_id: str) -> Recommendation:
        """Return the ORM recommendation model."""
        recommendation = self.session.get(Recommendation, recommendation_id)
        if recommendation is None:
            raise ResourceNotFoundError(
                code="RECOMMENDATION_NOT_FOUND",
                message=f"Recommendation {recommendation_id} was not found",
            )
        return recommendation

    def get_by_execution_id(self, execution_id: str) -> Recommendation | None:
        """Return recommendation linked to an analysis execution."""
        statement = select(Recommendation).where(
            Recommendation.analysis_execution_id == execution_id
        )
        return self.session.exec(statement).first()

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
        customer_id: str | None = None,
        status: RecommendationStatus | None = None,
        decision: RecommendationDecision | None = None,
        minimum_priority: float | None = None,
        sort_by: RecommendationSortField = "created_at",
        sort_order: SortOrder = "desc",
    ) -> PaginatedResponse[RecommendationSummary]:
        """Return paginated recommendations with optional filters."""
        validate_pagination(page, page_size)
        if sort_by == "created_at":
            order_column = Recommendation.created_at
        elif sort_by == "priority_score":
            order_column = Recommendation.priority_score
        else:
            raise UnsupportedSortFieldError(
                message=f"Unsupported sort field: {sort_by}",
                details={"sort_by": sort_by},
            )

        order_expression = order_column.asc() if sort_order == "asc" else order_column.desc()
        statement = select(Recommendation).order_by(order_expression)
        if customer_id is not None:
            statement = statement.where(Recommendation.customer_id == customer_id)
        if status is not None:
            statement = statement.where(Recommendation.status == status)
        if decision is not None:
            statement = statement.where(Recommendation.decision == decision)
        if minimum_priority is not None:
            statement = statement.where(Recommendation.priority_score >= minimum_priority)
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
