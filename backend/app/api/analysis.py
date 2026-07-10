"""Rules-only analysis API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.schemas.analysis import RulesOnlyAnalysisResponse
from app.schemas.common import ApiErrorResponse
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/analysis", tags=["analysis"])

NOT_FOUND_RESPONSE = {
    404: {
        "model": ApiErrorResponse,
        "description": "Customer not found",
    }
}


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
