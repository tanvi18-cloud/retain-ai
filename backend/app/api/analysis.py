"""Analysis execution API routes."""

from typing import Annotated, Literal

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlmodel import Session

from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.models.enums import AnalysisExecutionMode, AnalysisExecutionStatus
from app.schemas.analysis import RulesOnlyAnalysisResponse
from app.schemas.analysis_execution import (
    AnalysisExecutionAcceptedResponse,
    AnalysisExecutionCreateRequest,
    AnalysisExecutionDetail,
    AnalysisExecutionSummary,
)
from app.schemas.common import ApiErrorResponse, PaginatedResponse
from app.services.analysis_execution_service import AnalysisExecutionService
from app.services.analysis_runner import run_analysis_background
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/analysis", tags=["analysis"])

NOT_FOUND_RESPONSE = {
    404: {
        "model": ApiErrorResponse,
        "description": "Customer or execution not found",
    }
}

SortOrder = Literal["asc", "desc"]


@router.post(
    "/{customer_id}/rules-only",
    response_model=RulesOnlyAnalysisResponse,
    summary="Run rules-only customer analysis",
    description=(
        "Run synchronous deterministic analysis including churn scoring, value scoring, "
        "priority calculation, offer eligibility, and financial projections. "
        "Does not persist recommendations or invoke an LLM."
    ),
    responses=NOT_FOUND_RESPONSE,
)
def analyze_customer_rules_only(
    customer_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> RulesOnlyAnalysisResponse:
    """Return rules-only analysis for a customer."""
    service = AnalysisService(session)
    return service.analyze_customer_rules_only(customer_id)


@router.post(
    "/{customer_id}",
    response_model=AnalysisExecutionAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue agentic customer analysis",
    description=(
        "Create an analysis execution and queue the retention flow asynchronously. "
        "Returns immediately with an execution ID for polling."
    ),
    responses=NOT_FOUND_RESPONSE,
)
def queue_customer_analysis(
    customer_id: str,
    body: AnalysisExecutionCreateRequest,
    background_tasks: BackgroundTasks,
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AnalysisExecutionAcceptedResponse:
    """Queue a retention flow execution for a customer."""
    execution_service = AnalysisExecutionService(session)

    if body.idempotency_key and not body.force_reanalysis:
        existing = execution_service.find_by_idempotency_key(body.idempotency_key)
        if existing is not None:
            session.commit()
            return AnalysisExecutionAcceptedResponse(
                execution_id=existing.id,
                customer_id=existing.customer_id,
                status=existing.status,
                queued_at=existing.created_at,
                status_url=f"/api/v1/analysis/executions/{existing.id}",
            )

    execution = execution_service.create_execution(
        customer_id=customer_id,
        mode=AnalysisExecutionMode.AGENTIC,
        idempotency_key=body.idempotency_key,
    )
    session.commit()

    background_tasks.add_task(
        run_analysis_background,
        execution_id=execution.id,
        customer_id=customer_id,
        notifications_enabled=body.notifications_enabled,
        database_url=settings.database_url,
    )

    return AnalysisExecutionAcceptedResponse(
        execution_id=execution.id,
        customer_id=customer_id,
        status=AnalysisExecutionStatus.QUEUED,
        queued_at=execution.created_at,
        status_url=f"/api/v1/analysis/executions/{execution.id}",
    )


@router.get(
    "/executions/{execution_id}",
    response_model=AnalysisExecutionDetail,
    summary="Get analysis execution status",
    responses=NOT_FOUND_RESPONSE,
)
def get_analysis_execution(
    execution_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> AnalysisExecutionDetail:
    """Return analysis execution detail."""
    service = AnalysisExecutionService(session)
    return service.get_detail(execution_id)


@router.get(
    "/executions",
    response_model=PaginatedResponse[AnalysisExecutionSummary],
    summary="List analysis executions",
)
def list_analysis_executions(
    session: Annotated[Session, Depends(get_session)],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    customer_id: Annotated[str | None, Query(description="Filter by customer ID")] = None,
    event_id: Annotated[str | None, Query(description="Filter by event ID")] = None,
    status: Annotated[
        AnalysisExecutionStatus | None,
        Query(description="Filter by execution status"),
    ] = None,
    mode: Annotated[
        AnalysisExecutionMode | None,
        Query(description="Filter by execution mode"),
    ] = None,
    sort_order: Annotated[SortOrder, Query(description="Sort direction by created_at")] = "desc",
) -> PaginatedResponse[AnalysisExecutionSummary]:
    """Return paginated analysis executions."""
    service = AnalysisExecutionService(session)
    return service.list_executions(
        page=page,
        page_size=page_size,
        customer_id=customer_id,
        event_id=event_id,
        status=status,
        mode=mode,
        sort_order=sort_order,
    )
