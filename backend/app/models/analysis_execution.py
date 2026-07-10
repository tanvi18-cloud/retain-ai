"""Analysis execution tracking for rules-only and agentic runs."""

from datetime import datetime

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.base import TimestampMixin, new_uuid
from app.models.enums import AnalysisExecutionMode, AnalysisExecutionStatus


class AnalysisExecution(TimestampMixin, SQLModel, table=True):
    """Tracks a customer analysis run from queue through completion."""

    __tablename__ = "analysis_executions"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_analysis_executions_idempotency_key"),
    )

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=36)
    customer_id: str = Field(
        foreign_key="customers.customer_id",
        nullable=False,
        index=True,
        max_length=32,
    )
    event_id: str | None = Field(
        default=None,
        foreign_key="incoming_events.id",
        nullable=True,
        index=True,
        max_length=36,
    )
    mode: AnalysisExecutionMode = Field(nullable=False, index=True)
    status: AnalysisExecutionStatus = Field(
        default=AnalysisExecutionStatus.QUEUED,
        nullable=False,
        index=True,
    )
    current_step: str | None = Field(default=None, max_length=128, nullable=True)
    priority_score: int | None = Field(default=None, nullable=True)
    recommendation_id: str | None = Field(
        default=None,
        nullable=True,
        index=True,
        max_length=36,
    )
    idempotency_key: str | None = Field(default=None, max_length=128, nullable=True, index=True)
    error_code: str | None = Field(default=None, max_length=64, nullable=True)
    safe_error_message: str | None = Field(default=None, max_length=512, nullable=True)
    started_at: datetime | None = Field(default=None, nullable=True)
    completed_at: datetime | None = Field(default=None, nullable=True)
    execution_metadata_json: dict = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
    )
    validation_warnings_json: list = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
