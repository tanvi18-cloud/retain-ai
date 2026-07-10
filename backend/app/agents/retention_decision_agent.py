"""Retention Decision CrewAI agent."""

from __future__ import annotations

from app.agents.prompts import (
    RETENTION_DECISION_BACKSTORY,
    RETENTION_DECISION_GOAL,
    RETENTION_DECISION_ROLE,
    RETENTION_DECISION_TASK,
)
from app.core.config import Settings, get_settings
from app.core.exceptions import AgentValidationFailedError
from app.core.llm import create_agent, execute_structured_task
from app.schemas.agent_outputs import RetentionDecisionOutput, SignalInvestigation
from app.services.agent_validation_service import AgentValidationService
from app.services.mock_llm_service import MockLLMService
from app.tools import RETENTION_DECISION_TOOLS


def create_retention_decision_agent(settings: Settings | None = None):
    """Create the Retention Decision Specialist CrewAI agent."""
    resolved = settings or get_settings()
    return create_agent(
        role=RETENTION_DECISION_ROLE,
        goal=RETENTION_DECISION_GOAL,
        backstory=RETENTION_DECISION_BACKSTORY,
        tools=RETENTION_DECISION_TOOLS,
        settings=resolved,
    )


def run_retention_decision(
    customer_id: str,
    investigation: SignalInvestigation | None = None,
    *,
    settings: Settings | None = None,
) -> RetentionDecisionOutput:
    """Run the Retention Decision agent and return validated structured output."""
    resolved = settings or get_settings()
    normalized_id = customer_id.strip().upper()
    validator = AgentValidationService(resolved)

    if resolved.mock_llm_mode:
        output = MockLLMService(resolved).retention_decision(normalized_id, investigation)
    else:
        agent = create_retention_decision_agent(resolved)
        description = RETENTION_DECISION_TASK.format(customer_id=normalized_id)
        if investigation is not None:
            description = (
                f"{description}\nPrior investigation summary: "
                f"{investigation.investigation_summary}"
            )
        output = execute_structured_task(
            agent=agent,
            description=description,
            expected_output="Structured RetentionDecisionOutput JSON",
            output_model=RetentionDecisionOutput,
            inputs={"customer_id": normalized_id},
            settings=resolved,
        )

    result = validator.validate_retention_decision(normalized_id, output)
    if not result.valid:
        raise AgentValidationFailedError(
            message="Retention decision failed validation",
            details={"errors": result.errors},
        )
    if result.warnings and output.agent_supported_decision != output.deterministic_decision:
        output = output.model_copy(
            update={"agent_supported_decision": output.deterministic_decision}
        )
    return output
