"""Offer persistence operations."""

from sqlmodel import Session, select

from app.core.exceptions import ResourceNotFoundError
from app.models.offer import Offer
from app.schemas.common import PaginatedResponse
from app.schemas.offers import OfferDetail, OfferSummary
from app.services.repository_utils import count_query, paginate_offset, validate_pagination


def _to_summary(offer: Offer) -> OfferSummary:
    return OfferSummary.model_validate(offer)


def _to_detail(offer: Offer) -> OfferDetail:
    return OfferDetail.model_validate(offer)


class OfferRepository:
    """Data access for approved offers."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, offer_id: str) -> OfferDetail:
        """Return an offer by ID or raise when not found."""
        offer = self.session.get(Offer, offer_id)
        if offer is None:
            raise ResourceNotFoundError(
                code="OFFER_NOT_FOUND",
                message=f"Offer {offer_id} was not found",
            )
        return _to_detail(offer)

    def list_active_offers(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[OfferSummary]:
        """Return a paginated list of active offers."""
        validate_pagination(page, page_size)
        statement = select(Offer).where(Offer.active.is_(True)).order_by(Offer.offer_id)
        total = count_query(self.session, statement)
        offers = self.session.exec(
            statement.offset(paginate_offset(page, page_size)).limit(page_size)
        ).all()
        return PaginatedResponse.build(
            items=[_to_summary(offer) for offer in offers],
            total=total,
            page=page,
            page_size=page_size,
        )

    def list_all_offers(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[OfferSummary]:
        """Return a paginated list of all offers."""
        validate_pagination(page, page_size)
        statement = select(Offer).order_by(Offer.offer_id)
        total = count_query(self.session, statement)
        offers = self.session.exec(
            statement.offset(paginate_offset(page, page_size)).limit(page_size)
        ).all()
        return PaginatedResponse.build(
            items=[_to_summary(offer) for offer in offers],
            total=total,
            page=page,
            page_size=page_size,
        )

    def list_all_active(self) -> list[OfferDetail]:
        """Return all active offers ordered by offer ID."""
        statement = select(Offer).where(Offer.active.is_(True)).order_by(Offer.offer_id)
        offers = self.session.exec(statement).all()
        return [_to_detail(offer) for offer in offers]
