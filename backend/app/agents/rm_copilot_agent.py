"""RM Copilot CrewAI agent."""

from __future__ import annotations

from app.agents.prompts import (
    RM_COPILOT_BACKSTORY,
    RM_COPILOT_GOAL,
    RM_COPILOT_ROLE,
    RM_COPILOT_TASK,
)
from app.core.config import Settings, get_settings
from app.core.exceptions import AgentValidationFailedError
from app.core.llm import create_agent, execute_structured_task
from app.schemas.agent_outputs import (
    OfferStrategyOutput,
    RetentionDecisionOutput,
    RMCopilotBrief,
    SignalInvestigation,
)
from app.services.agent_validation_service import AgentValidationService
from app.services.mock_llm_service import MockLLMService
from app.tools import RM_COPILOT_TOOLS


def create_rm_copilot_agent(settings: Settings | None = None):
    """Create the RM Copilot CrewAI agent."""
    resolved = settings or get_settings()
    return create_agent(
        role=RM_COPILOT_ROLE,
        goal=RM_COPILOT_GOAL,
        backstory=RM_COPILOT_BACKSTORY,
        tools=RM_COPILOT_TOOLS,
        settings=resolved,
    )


def run_rm_copilot(
    customer_id: str,
    investigation: SignalInvestigation | None = None,
    decision: RetentionDecisionOutput | None = None,
    offer_strategy: OfferStrategyOutput | None = None,
    *,
    settings: Settings | None = None,
) -> RMCopilotBrief:
    """Run the RM Copilot agent and return validated structured output."""
    resolved = settings or get_settings()
    normalized_id = customer_id.strip().upper()
    validator = AgentValidationService(resolved)

    if resolved.mock_llm_mode:
        output = MockLLMService(resolved).rm_copilot_brief(
            normalized_id,
            investigation,
            decision,
            offer_strategy,
        )
    else:
        agent = create_rm_copilot_agent(resolved)
        description = RM_COPILOT_TASK.format(customer_id=normalized_id)
        if offer_strategy is not None and offer_strategy.recommended_offer_id:
            description = f"{description}\nRecommended offer: {offer_strategy.recommended_offer_id}"
        output = execute_structured_task(
            agent=agent,
            description=description,
            expected_output="Structured RMCopilotBrief JSON",
            output_model=RMCopilotBrief,
            inputs={"customer_id": normalized_id},
            settings=resolved,
        )

    result = validator.validate_rm_copilot_brief(normalized_id, output)
    if not result.valid:
        raise AgentValidationFailedError(
            message="RM copilot brief failed validation",
            details={"errors": result.errors},
        )
    if result.warnings and not output.prohibited_claims:
        output = output.model_copy(
            update={"prohibited_claims": ["Do not promise product approval."]}
        )
    return output
