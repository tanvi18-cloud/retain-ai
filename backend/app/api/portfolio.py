"""Portfolio API routes."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.database import get_session
from app.models.enums import CustomerSegment, RecommendationDecision
from app.schemas.common import PaginatedResponse
from app.schemas.portfolio import PortfolioCustomerRow, PortfolioSummaryResponse
from app.services.portfolio_service import PortfolioService

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

PortfolioSortField = Literal[
    "customer_id",
    "full_name",
    "churn_score",
    "value_score",
    "priority_score",
    "revenue_at_risk",
    "expected_net_benefit",
]
SortOrder = Literal["asc", "desc"]


@router.get(
    "/summary",
    response_model=PortfolioSummaryResponse,
    summary="Get portfolio summary",
    description="Return portfolio-level retention metrics across all seeded customers.",
)
def get_portfolio_summary(
    session: Annotated[Session, Depends(get_session)],
) -> PortfolioSummaryResponse:
    """Return portfolio summary metrics."""
    service = PortfolioService(session)
    return service.get_summary()


@router.get(
    "/customers",
    response_model=PaginatedResponse[PortfolioCustomerRow],
    summary="List portfolio customers",
    description="Return a paginated portfolio customer table with scores and recommendations.",
)
def list_portfolio_customers(
    session: Annotated[Session, Depends(get_session)],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    search: Annotated[
        str | None,
        Query(description="Search by customer ID or full name"),
    ] = None,
    segment: Annotated[
        CustomerSegment | None,
        Query(description="Filter by segment"),
    ] = None,
    decision: Annotated[
        RecommendationDecision | None,
        Query(description="Filter by retention decision"),
    ] = None,
    trigger_type: Annotated[
        str | None,
        Query(description="Filter by primary trigger rule code"),
    ] = None,
    minimum_priority: Annotated[
        int | None,
        Query(ge=0, le=100, description="Minimum priority score"),
    ] = None,
    sort_by: Annotated[PortfolioSortField, Query(description="Sort field")] = "priority_score",
    sort_order: Annotated[SortOrder, Query(description="Sort direction")] = "desc",
) -> PaginatedResponse[PortfolioCustomerRow]:
    """Return paginated portfolio customer rows."""
    service = PortfolioService(session)
    return service.list_customers(
        page=page,
        page_size=page_size,
        search=search,
        segment=segment,
        decision=decision,
        trigger_type=trigger_type,
        minimum_priority=minimum_priority,
        sort_by=sort_by,
        sort_order=sort_order,
    )
