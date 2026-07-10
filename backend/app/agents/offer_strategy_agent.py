"""Offer Strategy CrewAI agent."""

from __future__ import annotations

from app.agents.prompts import (
    OFFER_STRATEGY_BACKSTORY,
    OFFER_STRATEGY_GOAL,
    OFFER_STRATEGY_ROLE,
    OFFER_STRATEGY_TASK,
)
from app.core.config import Settings, get_settings
from app.core.exceptions import AgentValidationFailedError
from app.core.llm import create_agent, execute_structured_task
from app.schemas.agent_outputs import (
    OfferStrategyOutput,
    RetentionDecisionOutput,
    SignalInvestigation,
)
from app.services.agent_validation_service import AgentValidationService
from app.services.mock_llm_service import MockLLMService
from app.tools import OFFER_STRATEGY_TOOLS


def create_offer_strategy_agent(settings: Settings | None = None):
    """Create the Offer Strategy Specialist CrewAI agent."""
    resolved = settings or get_settings()
    return create_agent(
        role=OFFER_STRATEGY_ROLE,
        goal=OFFER_STRATEGY_GOAL,
        backstory=OFFER_STRATEGY_BACKSTORY,
        tools=OFFER_STRATEGY_TOOLS,
        settings=resolved,
    )


def run_offer_strategy(
    customer_id: str,
    investigation: SignalInvestigation | None = None,
    decision: RetentionDecisionOutput | None = None,
    *,
    settings: Settings | None = None,
) -> OfferStrategyOutput:
    """Run the Offer Strategy agent and return validated structured output."""
    resolved = settings or get_settings()
    normalized_id = customer_id.strip().upper()
    validator = AgentValidationService(resolved)

    if resolved.mock_llm_mode:
        output = MockLLMService(resolved).offer_strategy(normalized_id, investigation, decision)
    else:
        agent = create_offer_strategy_agent(resolved)
        description = OFFER_STRATEGY_TASK.format(customer_id=normalized_id)
        if investigation is not None:
            description = f"{description}\nPrimary signal: {investigation.primary_signal}"
        if decision is not None:
            description = f"{description}\nDecision: {decision.deterministic_decision.value}"
        output = execute_structured_task(
            agent=agent,
            description=description,
            expected_output="Structured OfferStrategyOutput JSON",
            output_model=OfferStrategyOutput,
            inputs={"customer_id": normalized_id},
            settings=resolved,
        )

    result = validator.validate_offer_strategy(normalized_id, output)
    if not result.valid:
        raise AgentValidationFailedError(
            message="Offer strategy failed validation",
            details={"errors": result.errors},
        )
    if result.warnings:
        from app.core.agent_policy import AGENT_ELIGIBILITY_DISCLAIMER

        if any("disclaimer" in warning.lower() for warning in result.warnings):
            output = output.model_copy(
                update={"eligibility_disclaimer": AGENT_ELIGIBILITY_DISCLAIMER}
            )
    return output
