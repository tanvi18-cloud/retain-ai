"""Signal Investigator CrewAI agent."""

from __future__ import annotations

from app.agents.prompts import (
    SIGNAL_INVESTIGATOR_BACKSTORY,
    SIGNAL_INVESTIGATOR_GOAL,
    SIGNAL_INVESTIGATOR_ROLE,
    SIGNAL_INVESTIGATOR_TASK,
)
from app.core.config import Settings, get_settings
from app.core.exceptions import AgentValidationFailedError
from app.core.llm import create_agent, execute_structured_task
from app.schemas.agent_outputs import SignalInvestigation
from app.services.agent_validation_service import AgentValidationService
from app.services.mock_llm_service import MockLLMService
from app.tools import SIGNAL_INVESTIGATOR_TOOLS


def create_signal_investigator_agent(settings: Settings | None = None):
    """Create the Signal Investigator CrewAI agent."""
    resolved = settings or get_settings()
    return create_agent(
        role=SIGNAL_INVESTIGATOR_ROLE,
        goal=SIGNAL_INVESTIGATOR_GOAL,
        backstory=SIGNAL_INVESTIGATOR_BACKSTORY,
        tools=SIGNAL_INVESTIGATOR_TOOLS,
        settings=resolved,
    )


def run_signal_investigator(
    customer_id: str,
    context: str | None = None,
    *,
    settings: Settings | None = None,
) -> SignalInvestigation:
    """Run the Signal Investigator and return validated structured output."""
    resolved = settings or get_settings()
    normalized_id = customer_id.strip().upper()
    validator = AgentValidationService(resolved)

    if resolved.mock_llm_mode:
        output = MockLLMService(resolved).signal_investigation(normalized_id)
    else:
        agent = create_signal_investigator_agent(resolved)
        description = SIGNAL_INVESTIGATOR_TASK.format(customer_id=normalized_id)
        if context:
            description = f"{description}\nAdditional context: {context}"
        output = execute_structured_task(
            agent=agent,
            description=description,
            expected_output="Structured SignalInvestigation JSON",
            output_model=SignalInvestigation,
            inputs={"customer_id": normalized_id},
            settings=resolved,
        )

    result = validator.validate_signal_investigation(normalized_id, output)
    if not result.valid:
        raise AgentValidationFailedError(
            message="Signal investigation failed validation",
            details={"errors": result.errors},
        )
    return output
