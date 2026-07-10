"""Analysis execution API schemas."""

from datetime import datetime

from pydantic import Field

from app.models.enums import AnalysisExecutionMode, AnalysisExecutionStatus
from app.schemas.common import APIModel


class AnalysisExecutionCreateRequest(APIModel):
    """Request body for manual customer analysis."""

    notifications_enabled: bool = True
    force_reanalysis: bool = False
    reason: str | None = Field(default=None, max_length=512)
    idempotency_key: str | None = Field(default=None, max_length=128)


class AnalysisExecutionAcceptedResponse(APIModel):
    """202 response when analysis is queued."""

    execution_id: str
    customer_id: str
    status: AnalysisExecutionStatus
    queued_at: datetime
    status_url: str


class AnalysisExecutionDetail(APIModel):
    """Analysis execution status detail."""

    execution_id: str
    customer_id: str
    event_id: str | None
    mode: AnalysisExecutionMode
    status: AnalysisExecutionStatus
    current_step: str | None
    recommendation_id: str | None
    priority_score: int | None
    started_at: datetime | None
    completed_at: datetime | None
    error_code: str | None
    safe_error_message: str | None
    validation_warnings: list[str]
    status_url: str
    recommendation_url: str | None = None
    created_at: datetime
    updated_at: datetime


class AnalysisExecutionSummary(APIModel):
    """Compact analysis execution listing item."""

    execution_id: str
    customer_id: str
    event_id: str | None
    mode: AnalysisExecutionMode
    status: AnalysisExecutionStatus
    priority_score: int | None
    recommendation_id: str | None
    created_at: datetime
