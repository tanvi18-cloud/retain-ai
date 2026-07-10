"""Customer API routes."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.database import get_session
from app.models.enums import CustomerSegment
from app.schemas.common import ApiErrorResponse, PaginatedResponse
from app.schemas.customer_360 import Customer360Response
from app.schemas.customers import CustomerDetail, CustomerSummary
from app.services.customer_360_service import Customer360Service
from app.services.customer_repository import CustomerRepository

router = APIRouter(prefix="/customers", tags=["customers"])

NOT_FOUND_RESPONSE = {
    404: {
        "model": ApiErrorResponse,
        "description": "Customer not found",
    }
}

CustomerSortField = Literal[
    "customer_id",
    "full_name",
    "relationship_start_date",
    "estimated_annual_value",
]
SortOrder = Literal["asc", "desc"]


@router.get(
    "",
    response_model=PaginatedResponse[CustomerSummary],
    summary="List customers",
    description="Return a paginated list of synthetic retail banking customers.",
)
def list_customers(
    session: Annotated[Session, Depends(get_session)],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    segment: Annotated[
        CustomerSegment | None,
        Query(description="Filter by segment"),
    ] = None,
    search: Annotated[
        str | None,
        Query(description="Search by customer ID or full name"),
    ] = None,
    sort_by: Annotated[CustomerSortField, Query(description="Sort field")] = "customer_id",
    sort_order: Annotated[SortOrder, Query(description="Sort direction")] = "asc",
) -> PaginatedResponse[CustomerSummary]:
    """List customers with pagination, filtering, and sorting."""
    repository = CustomerRepository(session)
    return repository.list_customers(
        page=page,
        page_size=page_size,
        segment=segment,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get(
    "/{customer_id}",
    response_model=CustomerDetail,
    summary="Get customer detail",
    description="Return the full customer profile for a single customer.",
    responses=NOT_FOUND_RESPONSE,
)
def get_customer(
    customer_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> CustomerDetail:
    """Return a customer detail record."""
    repository = CustomerRepository(session)
    return repository.get_by_id(customer_id)


@router.get(
    "/{customer_id}/360",
    response_model=Customer360Response,
    summary="Get Customer 360 view",
    description=(
        "Return an aggregated Customer 360 view including accounts, credit profile, "
        "bureau triggers, transaction features, recommendations, interactions, "
        "freshness metadata, and non-fatal data warnings."
    ),
    responses=NOT_FOUND_RESPONSE,
)
def get_customer_360(
    customer_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> Customer360Response:
    """Return the Customer 360 aggregation for a customer."""
    service = Customer360Service(session)
    return service.get_customer_360(customer_id)
