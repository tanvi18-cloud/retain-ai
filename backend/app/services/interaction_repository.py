"""Interaction persistence operations."""

from sqlmodel import Session, select

from app.models.interaction import Interaction
from app.schemas.common import PaginatedResponse
from app.schemas.interactions import InteractionDetail, InteractionSummary
from app.services.repository_utils import count_query, paginate_offset, validate_pagination


def _to_summary(interaction: Interaction) -> InteractionSummary:
    return InteractionSummary(
        interaction_id=interaction.id,
        customer_id=interaction.customer_id,
        recommendation_id=interaction.recommendation_id,
        rm_id=interaction.rm_id,
        action_type=interaction.action_type,
        offer_presented=interaction.offer_presented,
        created_at=interaction.created_at,
    )


def _to_detail(interaction: Interaction) -> InteractionDetail:
    return InteractionDetail(
        interaction_id=interaction.id,
        customer_id=interaction.customer_id,
        recommendation_id=interaction.recommendation_id,
        rm_id=interaction.rm_id,
        action_type=interaction.action_type,
        notes=interaction.notes,
        offer_presented=interaction.offer_presented,
        customer_response=interaction.customer_response,
        created_at=interaction.created_at,
    )


class InteractionRepository:
    """Data access for RM interaction records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def list_by_customer(
        self,
        customer_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[InteractionSummary]:
        """Return paginated interactions for a customer ordered by newest first."""
        validate_pagination(page, page_size)
        statement = (
            select(Interaction)
            .where(Interaction.customer_id == customer_id)
            .order_by(Interaction.created_at.desc())
        )
        total = count_query(self.session, statement)
        interactions = self.session.exec(
            statement.offset(paginate_offset(page, page_size)).limit(page_size)
        ).all()
        return PaginatedResponse.build(
            items=[_to_summary(interaction) for interaction in interactions],
            total=total,
            page=page,
            page_size=page_size,
        )

    def list_recent_by_customer(
        self,
        customer_id: str,
        *,
        limit: int = 10,
    ) -> list[InteractionDetail]:
        """Return the most recent interactions for a customer."""
        statement = (
            select(Interaction)
            .where(Interaction.customer_id == customer_id)
            .order_by(Interaction.created_at.desc())
            .limit(limit)
        )
        interactions = self.session.exec(statement).all()
        return [_to_detail(interaction) for interaction in interactions]
