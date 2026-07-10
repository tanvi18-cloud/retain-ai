"""Retention flow Pydantic state."""

from datetime import datetime

from app.schemas.agent_outputs import (
    OfferStrategyOutput,
    RetentionDecisionOutput,
    RMCopilotBrief,
    SignalInvestigation,
)
from app.schemas.analysis import OfferFinancialOption, RulesOnlyAnalysisResponse
from app.schemas.common import APIModel
from app.schemas.crew_result import FinalPolicyValidationResult, RetentionCrewResult
from app.schemas.customer_360 import Customer360Response
from app.schemas.eligibility import EligibilityResult
from app.schemas.scoring import PriorityResult, ScoreResult


class RetentionFlowState(APIModel):
    """Serializable state passed through the retention flow."""

    execution_id: str
    customer_id: str
    event_id: str | None = None
    notifications_enabled: bool = True
    customer_360: Customer360Response | None = None
    churn_result: ScoreResult | None = None
    value_result: ScoreResult | None = None
    priority_result: PriorityResult | None = None
    eligibility_result: EligibilityResult | None = None
    financial_options: list[OfferFinancialOption] = []
    rules_analysis: RulesOnlyAnalysisResponse | None = None
    crew_result: RetentionCrewResult | None = None
    investigation: SignalInvestigation | None = None
    decision_output: RetentionDecisionOutput | None = None
    offer_strategy: OfferStrategyOutput | None = None
    rm_brief: RMCopilotBrief | None = None
    final_validation: FinalPolicyValidationResult | None = None
    recommendation_id: str | None = None
    alert_id: str | None = None
    errors: list[str] = []
    warnings: list[str] = []
    current_step: str = "INITIALIZED"
    agentic_analysis_ran: bool = False
    started_at: datetime | None = None
    completed_at: datetime | None = None
