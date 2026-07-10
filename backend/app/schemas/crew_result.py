"""Retention crew result schemas."""

from datetime import datetime
from typing import Any

from app.schemas.agent_outputs import (
    AgentValidationResult,
    OfferStrategyOutput,
    RetentionDecisionOutput,
    RMCopilotBrief,
    SignalInvestigation,
)
from app.schemas.common import APIModel
from app.schemas.llm import LLMMode


class CrewExecutionMetadata(APIModel):
    """Safe metadata describing a retention crew run."""

    mode: LLMMode
    configured_model: str
    process_type: str = "sequential"
    task_count: int = 4
    duration_ms: int
    calculation_version: str
    eligibility_policy_version: str
    agent_policy_version: str
    crewai_version: str | None = None
    task_durations_ms: dict[str, int] = {}


class RetentionCrewResult(APIModel):
    """Structured output from the four-agent retention crew."""

    execution_id: str
    customer_id: str
    investigation: SignalInvestigation
    decision: RetentionDecisionOutput
    offer_strategy: OfferStrategyOutput
    rm_brief: RMCopilotBrief
    validation_result: AgentValidationResult | None = None
    execution_metadata: CrewExecutionMetadata
    validation_warnings: list[str] = []
    started_at: datetime
    completed_at: datetime


class FinalPolicyValidationResult(APIModel):
    """Result of final policy validation against deterministic analysis."""

    valid: bool
    corrected: bool
    errors: list[str]
    warnings: list[str]
    rejected_fields: list[str]
    corrected_fields: list[str]
    validated_at: datetime
    policy_version: str


class FlowResult(APIModel):
    """Outcome of a retention flow execution."""

    execution_id: str
    customer_id: str
    event_id: str | None = None
    decision: str
    priority_score: int
    recommendation_id: str | None = None
    alert_id: str | None = None
    notification_status: str | None = None
    status: str
    agentic_analysis_ran: bool
    validation_warnings: list[str] = []
    started_at: datetime
    completed_at: datetime
    flow_summary: dict[str, Any] = {}
