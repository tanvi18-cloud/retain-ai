"""Incoming event persistence operations."""

from sqlmodel import Session, select

from app.core.exceptions import ResourceNotFoundError
from app.models.event import IncomingEvent
from app.schemas.common import PaginatedResponse
from app.schemas.events import IncomingEventDetail, IncomingEventSummary
from app.services.repository_utils import count_query, paginate_offset, validate_pagination


def _to_summary(event: IncomingEvent) -> IncomingEventSummary:
    return IncomingEventSummary(
        event_id=event.id,
        customer_id=event.customer_id,
        event_type=event.event_type,
        source_system=event.source_system,
        status=event.status,
        created_at=event.created_at,
    )


def _to_detail(event: IncomingEvent) -> IncomingEventDetail:
    return IncomingEventDetail(
        event_id=event.id,
        customer_id=event.customer_id,
        event_type=event.event_type,
        source_system=event.source_system,
        payload_json=event.payload_json,
        status=event.status,
        error_message=event.error_message,
        created_at=event.created_at,
        processed_at=event.processed_at,
    )


class EventRepository:
    """Data access for inbound customer events."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, event_id: str) -> IncomingEventDetail:
        """Return an event by ID or raise when not found."""
        event = self.session.get(IncomingEvent, event_id)
        if event is None:
            raise ResourceNotFoundError(
                code="EVENT_NOT_FOUND",
                message=f"Event {event_id} was not found",
            )
        return _to_detail(event)

    def list_events(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[IncomingEventSummary]:
        """Return paginated events ordered by newest first."""
        validate_pagination(page, page_size)
        statement = select(IncomingEvent).order_by(IncomingEvent.created_at.desc())
        total = count_query(self.session, statement)
        events = self.session.exec(
            statement.offset(paginate_offset(page, page_size)).limit(page_size)
        ).all()
        return PaginatedResponse.build(
            items=[_to_summary(event) for event in events],
            total=total,
            page=page,
            page_size=page_size,
        )

    def list_by_customer(
        self,
        customer_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[IncomingEventSummary]:
        """Return paginated events for a customer ordered by newest first."""
        validate_pagination(page, page_size)
        statement = (
            select(IncomingEvent)
            .where(IncomingEvent.customer_id == customer_id)
            .order_by(IncomingEvent.created_at.desc())
        )
        total = count_query(self.session, statement)
        events = self.session.exec(
            statement.offset(paginate_offset(page, page_size)).limit(page_size)
        ).all()
        return PaginatedResponse.build(
            items=[_to_summary(event) for event in events],
            total=total,
            page=page,
            page_size=page_size,
        )
