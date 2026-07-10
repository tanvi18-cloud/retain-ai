"""Recommendation read and action API routes."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.database import get_session
from app.models.enums import RecommendationDecision, RecommendationStatus
from app.schemas.common import ApiErrorResponse, PaginatedResponse
from app.schemas.recommendation_actions import (
    RecommendationActionRequest,
    RecommendationActionResponse,
    RecommendationCloseRequest,
    RecommendationContactedRequest,
    RecommendationRejectRequest,
)
from app.schemas.recommendations import RecommendationDetail, RecommendationSummary
from app.services.recommendation_action_service import RecommendationActionService
from app.services.recommendation_repository import RecommendationRepository

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

NOT_FOUND_RESPONSE = {
    404: {
        "model": ApiErrorResponse,
        "description": "Recommendation not found",
    }
}

CONFLICT_RESPONSE = {
    409: {
        "model": ApiErrorResponse,
        "description": "Invalid status transition",
    }
}

RecommendationSortField = Literal["created_at", "priority_score"]
SortOrder = Literal["asc", "desc"]


@router.get(
    "",
    response_model=PaginatedResponse[RecommendationSummary],
    summary="List recommendations",
    description="Return a paginated list of persisted retention recommendations.",
)
def list_recommendations(
    session: Annotated[Session, Depends(get_session)],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    customer_id: Annotated[
        str | None,
        Query(description="Filter by customer ID"),
    ] = None,
    status: Annotated[
        RecommendationStatus | None,
        Query(description="Filter by recommendation status"),
    ] = None,
    decision: Annotated[
        RecommendationDecision | None,
        Query(description="Filter by retention decision"),
    ] = None,
    minimum_priority: Annotated[
        float | None,
        Query(ge=0, le=100, description="Minimum priority score"),
    ] = None,
    sort_by: Annotated[RecommendationSortField, Query(description="Sort field")] = "created_at",
    sort_order: Annotated[SortOrder, Query(description="Sort direction")] = "desc",
) -> PaginatedResponse[RecommendationSummary]:
    """Return paginated recommendations."""
    repository = RecommendationRepository(session)
    return repository.list_recommendations(
        page=page,
        page_size=page_size,
        customer_id=customer_id,
        status=status,
        decision=decision,
        minimum_priority=minimum_priority,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get(
    "/{recommendation_id}",
    response_model=RecommendationDetail,
    summary="Get recommendation detail",
    description="Return a single persisted recommendation by ID.",
    responses=NOT_FOUND_RESPONSE,
)
def get_recommendation(
    recommendation_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> RecommendationDetail:
    """Return recommendation detail."""
    repository = RecommendationRepository(session)
    return repository.get_by_id(recommendation_id)


@router.post(
    "/{recommendation_id}/review",
    response_model=RecommendationActionResponse,
    summary="Mark recommendation reviewed",
    responses={**NOT_FOUND_RESPONSE, **CONFLICT_RESPONSE},
)
def review_recommendation(
    recommendation_id: str,
    body: RecommendationActionRequest,
    session: Annotated[Session, Depends(get_session)],
) -> RecommendationActionResponse:
    """Mark a recommendation as reviewed."""
    service = RecommendationActionService(session)
    result = service.review(
        recommendation_id,
        rm_id=body.rm_id,
        notes=body.notes,
        idempotency_key=body.idempotency_key,
    )
    session.commit()
    return result


@router.post(
    "/{recommendation_id}/approve",
    response_model=RecommendationActionResponse,
    summary="Approve recommendation for RM discussion",
    responses={**NOT_FOUND_RESPONSE, **CONFLICT_RESPONSE},
)
def approve_recommendation(
    recommendation_id: str,
    body: RecommendationActionRequest,
    session: Annotated[Session, Depends(get_session)],
) -> RecommendationActionResponse:
    """Approve a recommendation for RM discussion."""
    service = RecommendationActionService(session)
    result = service.approve(
        recommendation_id,
        rm_id=body.rm_id,
        notes=body.notes,
        idempotency_key=body.idempotency_key,
    )
    session.commit()
    return result


@router.post(
    "/{recommendation_id}/reject",
    response_model=RecommendationActionResponse,
    summary="Reject recommendation",
    responses={**NOT_FOUND_RESPONSE, **CONFLICT_RESPONSE},
)
def reject_recommendation(
    recommendation_id: str,
    body: RecommendationRejectRequest,
    session: Annotated[Session, Depends(get_session)],
) -> RecommendationActionResponse:
    """Reject a recommendation with a required reason."""
    service = RecommendationActionService(session)
    result = service.reject(
        recommendation_id,
        rm_id=body.rm_id,
        rejection_reason=body.rejection_reason,
        notes=body.notes,
        idempotency_key=body.idempotency_key,
    )
    session.commit()
    return result


@router.post(
    "/{recommendation_id}/contacted",
    response_model=RecommendationActionResponse,
    summary="Record customer contact",
    responses={**NOT_FOUND_RESPONSE, **CONFLICT_RESPONSE},
)
def contacted_recommendation(
    recommendation_id: str,
    body: RecommendationContactedRequest,
    session: Annotated[Session, Depends(get_session)],
) -> RecommendationActionResponse:
    """Record that the RM contacted the customer."""
    service = RecommendationActionService(session)
    result = service.contacted(
        recommendation_id,
        rm_id=body.rm_id,
        notes=body.notes,
        offer_presented=body.offer_presented,
        customer_response=body.customer_response,
        contact_channel=body.contact_channel,
        follow_up_date=body.follow_up_date,
        idempotency_key=body.idempotency_key,
    )
    session.commit()
    return result


@router.post(
    "/{recommendation_id}/close",
    response_model=RecommendationActionResponse,
    summary="Close recommendation",
    responses={**NOT_FOUND_RESPONSE, **CONFLICT_RESPONSE},
)
def close_recommendation(
    recommendation_id: str,
    body: RecommendationCloseRequest,
    session: Annotated[Session, Depends(get_session)],
) -> RecommendationActionResponse:
    """Close a recommendation with a closing note."""
    service = RecommendationActionService(session)
    result = service.close(
        recommendation_id,
        rm_id=body.rm_id,
        closing_note=body.closing_note,
        idempotency_key=body.idempotency_key,
    )
    session.commit()
    return result
