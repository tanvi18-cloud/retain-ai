"""Incoming event persistence operations."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from sqlmodel import Session, select

from app.core.exceptions import ResourceNotFoundError
from app.models.enums import EventType, IncomingEventStatus
from app.models.event import IncomingEvent
from app.schemas.common import PaginatedResponse
from app.schemas.events import IncomingEventDetail, IncomingEventResponse, IncomingEventSummary
from app.services.repository_utils import count_query, paginate_offset, validate_pagination

SortOrder = Literal["asc", "desc"]


def _utc_now() -> datetime:
    return datetime.now(UTC)


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
        idempotency_key=event.idempotency_key,
        execution_id=event.execution_id,
        analysis_result_json=event.analysis_result_json,
        status=event.status,
        error_message=event.error_message,
        retry_count=event.retry_count,
        notifications_enabled=event.notifications_enabled,
        created_at=event.created_at,
        queued_at=event.queued_at,
        processing_started_at=event.processing_started_at,
        processed_at=event.processed_at,
    )


def _to_response(event: IncomingEvent, *, duplicate: bool = False) -> IncomingEventResponse:
    return IncomingEventResponse(
        event_id=event.id,
        customer_id=event.customer_id,
        event_type=EventType(event.event_type),
        source_system=event.source_system,
        status=event.status,
        execution_id=event.execution_id,
        created_at=event.created_at,
        queued_at=event.queued_at,
        processing_started_at=event.processing_started_at,
        processed_at=event.processed_at,
        error_message=event.error_message,
        duplicate=duplicate,
        analysis_summary=event.analysis_result_json,
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

    def get_model_by_id(self, event_id: str) -> IncomingEvent:
        """Return the ORM event model."""
        event = self.session.get(IncomingEvent, event_id)
        if event is None:
            raise ResourceNotFoundError(
                code="EVENT_NOT_FOUND",
                message=f"Event {event_id} was not found",
            )
        return event

    def get_by_idempotency_key(self, idempotency_key: str) -> IncomingEvent | None:
        """Return an existing event for an idempotency key."""
        statement = select(IncomingEvent).where(IncomingEvent.idempotency_key == idempotency_key)
        return self.session.exec(statement).first()

    def create_event(
        self,
        *,
        customer_id: str,
        event_type: str,
        source_system: str,
        payload_json: dict,
        idempotency_key: str | None = None,
        notifications_enabled: bool = True,
    ) -> IncomingEvent:
        """Persist a new inbound event."""
        event = IncomingEvent(
            customer_id=customer_id,
            event_type=event_type,
            source_system=source_system,
            payload_json=payload_json,
            idempotency_key=idempotency_key,
            notifications_enabled=notifications_enabled,
            status=IncomingEventStatus.RECEIVED,
        )
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return event

    def mark_queued(self, event: IncomingEvent) -> IncomingEvent:
        """Mark an event as queued."""
        event.status = IncomingEventStatus.QUEUED
        event.queued_at = _utc_now()
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return event

    def mark_retry(self, event: IncomingEvent) -> IncomingEvent:
        """Reset a failed event for retry."""
        event.status = IncomingEventStatus.RECEIVED
        event.error_message = None
        event.processing_started_at = None
        event.processed_at = None
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return event

    def list_events(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        customer_id: str | None = None,
        event_type: str | None = None,
        status: IncomingEventStatus | None = None,
        source_system: str | None = None,
        sort_order: SortOrder = "desc",
    ) -> PaginatedResponse[IncomingEventSummary]:
        """Return paginated events with optional filters."""
        validate_pagination(page, page_size)
        statement = select(IncomingEvent)
        if customer_id is not None:
            statement = statement.where(IncomingEvent.customer_id == customer_id)
        if event_type is not None:
            statement = statement.where(IncomingEvent.event_type == event_type)
        if status is not None:
            statement = statement.where(IncomingEvent.status == status)
        if source_system is not None:
            statement = statement.where(IncomingEvent.source_system == source_system)
        order = (
            IncomingEvent.created_at.desc()
            if sort_order == "desc"
            else IncomingEvent.created_at.asc()
        )
        statement = statement.order_by(order)
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
        return self.list_events(
            page=page,
            page_size=page_size,
            customer_id=customer_id,
        )

    def to_response(
        self, event: IncomingEvent, *, duplicate: bool = False
    ) -> IncomingEventResponse:
        """Convert an event model to an API response."""
        return _to_response(event, duplicate=duplicate)
