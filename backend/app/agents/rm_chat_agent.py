"""Qwen-powered RM chat agent."""

from __future__ import annotations

from sqlmodel import Session

from app.core.config import Settings, get_settings
from app.core.llm import create_agent, execute_structured_task
from app.schemas.chat import ChatContext, IntentDetectionResult, RMChatAgentOutput
from app.services.chat_suggestions import suggested_questions
from app.services.chat_tool_executor import execute_tools_for_intent
from app.tools.chat_tools import ALLOWED_CHAT_TOOLS

RM_CHAT_ROLE = "RM Retention Copilot"
RM_CHAT_GOAL = (
    "Help Relationship Managers understand customer retention risk, eligible offers, "
    "and recommended actions using only tool-backed facts."
)
RM_CHAT_BACKSTORY = (
    "You support bank RMs with concise, evidence-backed retention guidance. "
    "You never contact customers, approve products, or invent banking facts."
)


def create_rm_chat_agent(settings: Settings | None = None):
    """Create the RM chat CrewAI agent without write-capable tools."""
    resolved = settings or get_settings()
    return create_agent(
        role=RM_CHAT_ROLE,
        goal=RM_CHAT_GOAL,
        backstory=RM_CHAT_BACKSTORY,
        tools=[],
        settings=resolved,
    )


def run_rm_chat_agent(
    *,
    message: str,
    intent: IntentDetectionResult,
    context: ChatContext,
    settings: Settings,
    session: Session,
) -> RMChatAgentOutput:
    """Run Qwen chat using pre-fetched tool data for safety."""
    used, evidence, payloads = execute_tools_for_intent(session, intent, context, settings)

    tool_context = {
        tool_name: (
            payloads[tool_name].model_dump(mode="json")
            if hasattr(payloads[tool_name], "model_dump")
            else payloads[tool_name]
        )
        for tool_name in used
        if tool_name in payloads
    }

    description = (
        f"User message: {message}\n"
        f"Detected intent: {intent.intent.value}\n"
        f"Customer IDs: {', '.join(intent.customer_ids) or context.active_customer_id or 'none'}\n"
        f"Allowed tools used: {', '.join(used)}\n"
        f"Tool data (authoritative): {tool_context}\n"
        "Respond with concise RM guidance. Cite evidence. "
        "Do not invent facts. Include eligibility disclaimer when discussing offers."
    )

    agent = create_rm_chat_agent(settings)
    output = execute_structured_task(
        agent=agent,
        description=description,
        expected_output="Structured RMChatAgentOutput JSON",
        output_model=RMChatAgentOutput,
        inputs={"message": message},
        settings=settings,
    )

    customer_ids = intent.customer_ids or (
        [context.active_customer_id] if context.active_customer_id else []
    )
    return output.model_copy(
        update={
            "intent": intent.intent,
            "customer_ids": customer_ids,
            "used_tools": [tool for tool in output.used_tools if tool in ALLOWED_CHAT_TOOLS]
            or used,
            "evidence": output.evidence or evidence,
            "suggested_questions": output.suggested_questions
            or suggested_questions(intent.intent, customer_ids),
        }
    )
