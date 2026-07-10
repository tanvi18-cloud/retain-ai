"""Recommendation read API routes."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.database import get_session
from app.models.enums import RecommendationDecision, RecommendationStatus
from app.schemas.common import ApiErrorResponse, PaginatedResponse
from app.schemas.recommendations import RecommendationDetail, RecommendationSummary
from app.services.recommendation_repository import RecommendationRepository

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

NOT_FOUND_RESPONSE = {
    404: {
        "model": ApiErrorResponse,
        "description": "Recommendation not found",
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
