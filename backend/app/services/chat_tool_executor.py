"""Execute safe chat tools for a detected intent."""

from __future__ import annotations

from sqlmodel import Session

from app.core.config import Settings, get_settings
from app.models.enums import ChatIntent
from app.schemas.chat import ChatContext, ChatEvidence, IntentDetectionResult
from app.tools import chat_tools

INTENT_TOOL_MAP: dict[ChatIntent, list[str]] = {
    ChatIntent.CUSTOMER_RISK_EXPLANATION: [
        "get_chat_customer_risk_explanation",
        "get_chat_customer_summary",
    ],
    ChatIntent.CUSTOMER_OFFER_EXPLANATION: [
        "get_chat_customer_summary",
        "get_chat_customer_recommendation",
    ],
    ChatIntent.CUSTOMER_ELIGIBILITY_EXPLANATION: ["get_chat_customer_eligibility"],
    ChatIntent.CUSTOMER_COMPARISON: ["compare_customers"],
    ChatIntent.PRIORITY_CUSTOMER_LIST: ["get_chat_priority_customers"],
    ChatIntent.PORTFOLIO_SUMMARY: ["get_chat_portfolio_summary"],
    ChatIntent.TRIGGER_SEARCH: ["search_customers_by_trigger"],
    ChatIntent.REVENUE_AT_RISK: ["get_chat_portfolio_summary"],
    ChatIntent.RM_TALKING_POINTS: ["get_rm_talking_points"],
    ChatIntent.RECOMMENDATION_STATUS: ["get_recommendation_status"],
    ChatIntent.DATA_FRESHNESS: [
        "get_customer_data_freshness",
        "get_customers_with_stale_data",
    ],
    ChatIntent.DPD_EXPLANATION: [
        "get_chat_customer_risk_explanation",
        "get_chat_customer_eligibility",
    ],
    ChatIntent.FOLLOW_UP_QUESTION: [
        "get_chat_customer_summary",
        "get_chat_customer_recommendation",
    ],
    ChatIntent.GENERAL_HELP: [],
    ChatIntent.UNSUPPORTED: [],
}


def execute_tools_for_intent(
    session: Session,
    intent: IntentDetectionResult,
    context: ChatContext,
    settings: Settings | None = None,
) -> tuple[list[str], list[ChatEvidence], dict]:
    """Run bounded safe tools for the detected chat intent."""
    resolved = settings or get_settings()
    tools = INTENT_TOOL_MAP.get(intent.intent, [])[: resolved.chat_max_tool_calls]
    used: list[str] = []
    evidence: list[ChatEvidence] = []
    payloads: dict = {}
    customer_id = intent.customer_ids[0] if intent.customer_ids else context.active_customer_id

    for tool_name in tools:
        payload = None
        if tool_name == "get_chat_customer_summary" and customer_id:
            payload = chat_tools.get_chat_customer_summary(session, customer_id)
        elif tool_name == "get_chat_customer_risk_explanation" and customer_id:
            payload = chat_tools.get_chat_customer_risk_explanation(session, customer_id)
        elif tool_name == "get_chat_customer_eligibility" and customer_id:
            payload = chat_tools.get_chat_customer_eligibility(session, customer_id)
        elif tool_name == "get_chat_customer_recommendation" and customer_id:
            payload = chat_tools.get_chat_customer_recommendation(session, customer_id)
        elif tool_name == "get_recommendation_status" and customer_id:
            payload = chat_tools.get_recommendation_status(session, customer_id)
        elif tool_name == "get_rm_talking_points" and customer_id:
            payload = chat_tools.get_rm_talking_points(session, customer_id)
        elif tool_name == "get_chat_priority_customers":
            payload = chat_tools.get_chat_priority_customers(
                session,
                limit=intent.requested_limit or 10,
            )
        elif tool_name == "get_chat_portfolio_summary":
            payload = chat_tools.get_chat_portfolio_summary(session)
        elif tool_name == "search_customers_by_trigger" and intent.trigger_type:
            payload = chat_tools.search_customers_by_trigger(session, intent.trigger_type)
        elif tool_name == "compare_customers" and len(intent.customer_ids) >= 2:
            payload = chat_tools.compare_customers(session, intent.customer_ids)
        elif tool_name == "get_customer_data_freshness" and customer_id:
            payload = chat_tools.get_customer_data_freshness(session, customer_id)
        elif tool_name == "get_customers_with_stale_data":
            payload = chat_tools.get_customers_with_stale_data(
                session,
                limit=intent.requested_limit or 20,
            )

        if payload is None:
            continue
        payloads[tool_name] = payload
        used.append(tool_name)
        evidence.extend(
            chat_tools.build_evidence_from_tool(
                tool_name,
                payload,
                customer_id=customer_id,
            )
        )

    return used, evidence, payloads
