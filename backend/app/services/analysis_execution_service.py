"""Analysis execution persistence and lifecycle."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from sqlmodel import Session, select

from app.core.exceptions import AnalysisExecutionNotFoundError
from app.models.analysis_execution import AnalysisExecution
from app.models.enums import AnalysisExecutionMode, AnalysisExecutionStatus
from app.schemas.analysis_execution import AnalysisExecutionDetail, AnalysisExecutionSummary
from app.schemas.common import PaginatedResponse
from app.services.customer_repository import CustomerRepository
from app.services.repository_utils import count_query, paginate_offset, validate_pagination

SortOrder = Literal["asc", "desc"]


def _utc_now() -> datetime:
    return datetime.now(UTC)


class AnalysisExecutionService:
    """Manage analysis execution records."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.customers = CustomerRepository(session)

    def create_execution(
        self,
        *,
        customer_id: str,
        mode: AnalysisExecutionMode,
        event_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> AnalysisExecution:
        """Create a new analysis execution after validating customer."""
        self.customers.get_by_id(customer_id)
        if idempotency_key:
            existing = self.find_by_idempotency_key(idempotency_key)
            if existing is not None:
                return existing
        execution = AnalysisExecution(
            customer_id=customer_id,
            event_id=event_id,
            mode=mode,
            status=AnalysisExecutionStatus.QUEUED,
            idempotency_key=idempotency_key,
        )
        self.session.add(execution)
        self.session.flush()
        return execution

    def find_by_idempotency_key(self, idempotency_key: str) -> AnalysisExecution | None:
        statement = select(AnalysisExecution).where(
            AnalysisExecution.idempotency_key == idempotency_key
        )
        return self.session.exec(statement).first()

    def get_by_id(self, execution_id: str) -> AnalysisExecution:
        execution = self.session.get(AnalysisExecution, execution_id)
        if execution is None:
            raise AnalysisExecutionNotFoundError(
                message=f"Analysis execution {execution_id} was not found",
            )
        return execution

    def get_detail(self, execution_id: str) -> AnalysisExecutionDetail:
        execution = self.get_by_id(execution_id)
        return self._to_detail(execution)

    def mark_running(self, execution: AnalysisExecution, *, current_step: str) -> AnalysisExecution:
        execution.status = AnalysisExecutionStatus.RUNNING
        execution.current_step = current_step
        execution.started_at = execution.started_at or _utc_now()
        self.session.add(execution)
        self.session.flush()
        return execution

    def update_step(self, execution: AnalysisExecution, step: str) -> AnalysisExecution:
        execution.current_step = step
        self.session.add(execution)
        self.session.flush()
        return execution

    def mark_completed(
        self,
        execution: AnalysisExecution,
        *,
        recommendation_id: str | None,
        priority_score: int | None,
        metadata: dict | None = None,
        validation_warnings: list[str] | None = None,
    ) -> AnalysisExecution:
        execution.status = AnalysisExecutionStatus.COMPLETED
        execution.recommendation_id = recommendation_id
        execution.priority_score = priority_score
        execution.completed_at = _utc_now()
        execution.current_step = "COMPLETED"
        if metadata:
            execution.execution_metadata_json = metadata
        if validation_warnings is not None:
            execution.validation_warnings_json = validation_warnings
        self.session.add(execution)
        self.session.flush()
        return execution

    def mark_failed(
        self,
        execution: AnalysisExecution,
        *,
        error_code: str,
        safe_error_message: str,
    ) -> AnalysisExecution:
        execution.status = AnalysisExecutionStatus.FAILED
        execution.error_code = error_code
        execution.safe_error_message = safe_error_message[:512]
        execution.completed_at = _utc_now()
        execution.current_step = "FAILED"
        self.session.add(execution)
        self.session.flush()
        return execution

    def find_by_event_id(self, event_id: str) -> AnalysisExecution | None:
        statement = (
            select(AnalysisExecution)
            .where(AnalysisExecution.event_id == event_id)
            .order_by(AnalysisExecution.created_at.desc())
        )
        return self.session.exec(statement).first()

    def list_executions(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        customer_id: str | None = None,
        event_id: str | None = None,
        status: AnalysisExecutionStatus | None = None,
        mode: AnalysisExecutionMode | None = None,
        sort_order: SortOrder = "desc",
    ) -> PaginatedResponse[AnalysisExecutionSummary]:
        validate_pagination(page, page_size)
        statement = select(AnalysisExecution)
        if customer_id is not None:
            statement = statement.where(AnalysisExecution.customer_id == customer_id)
        if event_id is not None:
            statement = statement.where(AnalysisExecution.event_id == event_id)
        if status is not None:
            statement = statement.where(AnalysisExecution.status == status)
        if mode is not None:
            statement = statement.where(AnalysisExecution.mode == mode)
        order = (
            AnalysisExecution.created_at.desc()
            if sort_order == "desc"
            else AnalysisExecution.created_at.asc()
        )
        statement = statement.order_by(order)
        total = count_query(self.session, statement)
        rows = self.session.exec(
            statement.offset(paginate_offset(page, page_size)).limit(page_size)
        ).all()
        return PaginatedResponse.build(
            items=[self._to_summary(row) for row in rows],
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
    ) -> PaginatedResponse[AnalysisExecutionSummary]:
        return self.list_executions(page=page, page_size=page_size, customer_id=customer_id)

    @staticmethod
    def _to_summary(execution: AnalysisExecution) -> AnalysisExecutionSummary:
        return AnalysisExecutionSummary(
            execution_id=execution.id,
            customer_id=execution.customer_id,
            event_id=execution.event_id,
            mode=execution.mode,
            status=execution.status,
            priority_score=execution.priority_score,
            recommendation_id=execution.recommendation_id,
            created_at=execution.created_at,
        )

    @staticmethod
    def _to_detail(execution: AnalysisExecution) -> AnalysisExecutionDetail:
        recommendation_url = None
        if execution.recommendation_id:
            recommendation_url = f"/api/v1/recommendations/{execution.recommendation_id}"
        return AnalysisExecutionDetail(
            execution_id=execution.id,
            customer_id=execution.customer_id,
            event_id=execution.event_id,
            mode=execution.mode,
            status=execution.status,
            current_step=execution.current_step,
            recommendation_id=execution.recommendation_id,
            priority_score=execution.priority_score,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            error_code=execution.error_code,
            safe_error_message=execution.safe_error_message,
            validation_warnings=list(execution.validation_warnings_json or []),
            status_url=f"/api/v1/analysis/executions/{execution.id}",
            recommendation_url=recommendation_url,
            created_at=execution.created_at,
            updated_at=execution.updated_at,
        )
