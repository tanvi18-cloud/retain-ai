"""Event ingestion and management API routes."""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import ValidationError
from sqlmodel import Session

from app.core.database import get_session
from app.core.exceptions import EventRetryNotAllowedError
from app.models.enums import EventType, IncomingEventStatus
from app.schemas.common import ApiErrorResponse, PaginatedResponse
from app.schemas.events import (
    IncomingEventCreate,
    IncomingEventDetail,
    IncomingEventResponse,
    IncomingEventSummary,
    validate_event_payload,
)
from app.services.audit_log_service import write_audit_log
from app.services.customer_repository import CustomerRepository
from app.services.event_queue import EventQueue
from app.services.event_repository import EventRepository

router = APIRouter(prefix="/events", tags=["events"])

NOT_FOUND_RESPONSE = {
    404: {
        "model": ApiErrorResponse,
        "description": "Resource not found",
    }
}

SortOrder = Literal["asc", "desc"]


def _get_event_queue(request: Request) -> EventQueue:
    queue = getattr(request.app.state, "event_queue", None)
    if queue is None:
        msg = "Event queue is not initialized"
        raise RuntimeError(msg)
    return queue


@router.post(
    "",
    response_model=IncomingEventResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest inbound event",
    description="Validate and asynchronously queue an inbound customer event.",
    responses=NOT_FOUND_RESPONSE,
)
async def ingest_event(
    payload: IncomingEventCreate,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
) -> IncomingEventResponse:
    """Accept an event for async processing."""
    CustomerRepository(session).get_by_id(payload.customer_id)

    if payload.idempotency_key:
        repository = EventRepository(session)
        existing = repository.get_by_idempotency_key(payload.idempotency_key)
        if existing is not None:
            return repository.to_response(existing, duplicate=True)

    try:
        validated_payload = validate_event_payload(payload.event_type, payload.payload)
    except ValidationError as exc:
        from fastapi.exceptions import RequestValidationError

        raise RequestValidationError(exc.errors()) from exc

    repository = EventRepository(session)
    event = repository.create_event(
        customer_id=payload.customer_id,
        event_type=payload.event_type.value,
        source_system=payload.source_system,
        payload_json=validated_payload,
        idempotency_key=payload.idempotency_key,
        notifications_enabled=payload.notifications_enabled,
    )
    event = repository.mark_queued(event)
    queue = _get_event_queue(request)
    await queue.enqueue(event.id)
    return repository.to_response(event)


@router.get(
    "",
    response_model=PaginatedResponse[IncomingEventSummary],
    summary="List events",
)
def list_events(
    session: Annotated[Session, Depends(get_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    customer_id: str | None = None,
    event_type: EventType | None = None,
    status: IncomingEventStatus | None = None,
    source_system: str | None = None,
    sort_order: SortOrder = "desc",
) -> PaginatedResponse[IncomingEventSummary]:
    """Return paginated inbound events."""
    repository = EventRepository(session)
    return repository.list_events(
        page=page,
        page_size=page_size,
        customer_id=customer_id,
        event_type=event_type.value if event_type else None,
        status=status,
        source_system=source_system,
        sort_order=sort_order,
    )


@router.get(
    "/{event_id}",
    response_model=IncomingEventDetail,
    summary="Get event detail",
    responses=NOT_FOUND_RESPONSE,
)
def get_event(
    event_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> IncomingEventDetail:
    """Return event detail."""
    return EventRepository(session).get_by_id(event_id)


@router.post(
    "/{event_id}/retry",
    response_model=IncomingEventResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Retry failed event",
    responses=NOT_FOUND_RESPONSE,
)
async def retry_event(
    event_id: str,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
) -> IncomingEventResponse:
    """Retry a failed event."""
    from app.core.config import get_settings

    settings = get_settings()
    repository = EventRepository(session)
    event = repository.get_model_by_id(event_id)
    if event.status != IncomingEventStatus.FAILED:
        raise EventRetryNotAllowedError(
            message="Only failed events can be retried",
            details={"event_id": event_id, "status": event.status.value},
        )
    if event.retry_count > settings.event_max_retries:
        raise EventRetryNotAllowedError(
            message="Event retry limit exceeded",
            details={"event_id": event_id, "retry_count": event.retry_count},
        )
    event = repository.mark_retry(event)
    event = repository.mark_queued(event)
    write_audit_log(
        session,
        entity_type="incoming_events",
        entity_id=event.id,
        action="EVENT_RETRY",
        actor_type="API",
        actor_id=None,
        details={"retry_count": event.retry_count},
    )
    session.commit()
    await _get_event_queue(request).enqueue(event.id)
    return repository.to_response(event)
