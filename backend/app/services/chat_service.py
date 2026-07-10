"""RM copilot chat orchestration."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlmodel import Session

from app.agents.rm_chat_agent import run_rm_chat_agent
from app.core.config import Settings, get_settings
from app.core.exceptions import (
    ChatServiceUnavailableError,
    ChatValidationFailedError,
    InvalidChatRequestError,
    ResourceNotFoundError,
)
from app.core.llm import check_qwen_availability
from app.core.policy_rules import C004_RESTRICTED_LENDING_OFFER_IDS
from app.core.scoring_rules import CHURN_BAND_HIGH_MAX
from app.models.enums import ChatIntent, ChatMessageRole
from app.schemas.chat import (
    VALID_CUSTOMER_IDS,
    ChatContext,
    ChatEvidence,
    ChatRequest,
    ChatResponse,
    ConversationDetail,
    IntentDetectionResult,
    RMChatAgentOutput,
)
from app.schemas.llm import LLMMode
from app.services.chat_context_service import ChatContextService
from app.services.chat_intent_service import ChatIntentService
from app.services.chat_repository import ChatRepository
from app.services.chat_suggestions import suggested_questions
from app.services.chat_tool_executor import execute_tools_for_intent
from app.services.chat_validation_service import ChatValidationService
from app.services.portfolio_service import PortfolioService
from app.tools import chat_tools


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _format_inr(amount: float) -> str:
    return f"INR {amount:,.2f}"


class ChatService:
    """Orchestrate RM copilot chat requests."""

    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.intent_service = ChatIntentService()
        self.context_service = ChatContextService(session, self.settings)
        self.repository = ChatRepository(session, self.settings)
        self.validator = ChatValidationService(session)

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Process an RM chat message and return a safe response."""
        if len(request.message) > self.settings.chat_max_message_length:
            raise InvalidChatRequestError(
                message="Message exceeds maximum length",
                details={"max_length": self.settings.chat_max_message_length},
            )
        if request.customer_id and request.customer_id not in VALID_CUSTOMER_IDS:
            raise ResourceNotFoundError(
                code="CUSTOMER_NOT_FOUND",
                message=f"Customer {request.customer_id} was not found",
            )

        conversation = self._load_or_create_conversation(request)
        context = self.context_service.resolve(
            conversation=conversation,
            explicit_customer_id=request.customer_id,
            include_history=request.include_history,
        )

        if context.ambiguous and context.clarification_question:
            return self._clarification_response(conversation, context, request)

        intent = self.intent_service.detect(
            request.message,
            has_active_customer=context.active_customer_id is not None,
        )
        intent = self._resolve_intent_customer(intent, context)

        if intent.requires_customer_context and not context.active_customer_id:
            return self._clarification_response(
                conversation,
                context,
                request,
                question=(
                    "Which customer should I review? "
                    "Please provide a customer ID such as C001."
                ),
            )

        if intent.intent == ChatIntent.UNSUPPORTED:
            return self._unsupported_response(conversation, intent, request)

        if self.settings.mock_llm_mode:
            output = self._mock_output(intent, context, request.message)
            mode = LLMMode.MOCK
        else:
            available, error = check_qwen_availability(self.settings)
            if not available:
                raise ChatServiceUnavailableError(
                    message="Qwen chat service is unavailable",
                    details={"error": error},
                )
            output = run_rm_chat_agent(
                message=request.message,
                intent=intent,
                context=context,
                settings=self.settings,
                session=self.session,
            )
            mode = LLMMode.QWEN

        portfolio_revenue = None
        if intent.intent == ChatIntent.REVENUE_AT_RISK:
            portfolio_revenue = PortfolioService(self.session).get_summary().total_revenue_at_risk

        validation = self.validator.validate_output(
            output,
            portfolio_total_revenue=portfolio_revenue,
        )
        if not validation.valid:
            raise ChatValidationFailedError(
                message="Chat response failed safety validation",
                details={"errors": validation.errors},
            )

        answer = validation.corrected_answer or output.answer
        warnings = list(validation.warnings)

        user_message = None
        assistant_message = None
        if self.settings.chat_history_enabled:
            user_message = self.repository.add_message(
                conversation_id=conversation.id,
                role=ChatMessageRole.USER,
                content=request.message,
                customer_ids=output.customer_ids or context.customer_ids,
            )
            assistant_message = self.repository.add_message(
                conversation_id=conversation.id,
                role=ChatMessageRole.ASSISTANT,
                content=answer,
                customer_ids=output.customer_ids,
                used_tools=output.used_tools,
                evidence=output.evidence,
                warnings=warnings,
            )
            if output.customer_ids:
                self.repository.update_active_customer(conversation, output.customer_ids[0])
            elif context.active_customer_id:
                self.repository.update_active_customer(conversation, context.active_customer_id)

        title = self._conversation_title(intent, output.customer_ids)
        if not conversation.title:
            self.repository.update_title(conversation, title)

        message_id = (
            assistant_message.id
            if assistant_message
            else user_message.id
            if user_message
            else str(uuid.uuid4())
        )

        return ChatResponse(
            conversation_id=conversation.id,
            message_id=message_id,
            answer=answer,
            intent=output.intent,
            customer_ids=output.customer_ids,
            used_tools=output.used_tools,
            evidence=output.evidence,
            warnings=warnings,
            suggested_questions=output.suggested_questions,
            generated_at=_utc_now(),
            mode=mode,
        )

    def list_conversations(self, **kwargs):
        return self.repository.list_conversations(**kwargs)

    def get_conversation_detail(
        self, conversation_id: str, *, rm_id: str
    ) -> ConversationDetail:
        conversation = self.context_service.get_conversation(conversation_id, rm_id=rm_id)
        messages = self.repository.list_recent_messages(
            conversation.id,
            limit=self.settings.chat_max_history_messages,
        )
        return ConversationDetail(
            conversation_id=conversation.id,
            rm_id=conversation.rm_id,
            title=conversation.title,
            active_customer_id=conversation.active_customer_id,
            status=conversation.status,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            expires_at=conversation.expires_at,
            messages=messages,
        )

    def close_conversation(self, conversation_id: str, *, rm_id: str) -> ConversationDetail:
        conversation = self.context_service.get_conversation(conversation_id, rm_id=rm_id)
        self.repository.close_conversation(conversation)
        return self.get_conversation_detail(conversation_id, rm_id=rm_id)

    def _load_or_create_conversation(self, request: ChatRequest):
        if request.conversation_id:
            return self.context_service.get_conversation(
                request.conversation_id,
                rm_id=request.rm_id,
            )
        return self.context_service.create_conversation(
            rm_id=request.rm_id,
            active_customer_id=request.customer_id,
        )

    def _resolve_intent_customer(
        self, intent: IntentDetectionResult, context: ChatContext
    ) -> IntentDetectionResult:
        customer_ids = list(intent.customer_ids)
        if not customer_ids and context.active_customer_id:
            customer_ids = [context.active_customer_id]
        return intent.model_copy(update={"customer_ids": customer_ids})

    def _execute_tools(
        self, intent: IntentDetectionResult, context: ChatContext
    ) -> tuple[list[str], list[ChatEvidence], dict]:
        return execute_tools_for_intent(self.session, intent, context, self.settings)

    def _mock_output(
        self,
        intent: IntentDetectionResult,
        context: ChatContext,
        message: str,
    ) -> RMChatAgentOutput:
        used, evidence, payloads = self._execute_tools(intent, context)
        customer_ids = list(intent.customer_ids)
        if not customer_ids and context.active_customer_id:
            customer_ids = [context.active_customer_id]

        if intent.intent == ChatIntent.GENERAL_HELP:
            answer = (
                "I help Relationship Managers review retention priorities, explain customer "
                "risk and eligibility, compare customers, draft talking points, and summarize "
                "portfolio exposure. Ask about a customer (C001–C010) or say "
                "'Who should I call today?'"
            )
            return RMChatAgentOutput(
                answer=answer,
                intent=ChatIntent.GENERAL_HELP,
                used_tools=[],
                suggested_questions=suggested_questions(ChatIntent.GENERAL_HELP, []),
                confidence=0.95,
            )

        answer = self._format_mock_answer(intent, payloads, message)
        return RMChatAgentOutput(
            answer=answer,
            intent=intent.intent,
            customer_ids=customer_ids,
            used_tools=used,
            evidence=evidence,
            warnings=list(context.context_warnings),
            suggested_questions=suggested_questions(intent.intent, customer_ids),
            confidence=intent.confidence,
        )

    def _format_mock_answer(
        self, intent: IntentDetectionResult, payloads: dict, message: str
    ) -> str:
        disclaimer = (
            "Eligibility indicates an RM discussion option and does not represent final "
            "credit or product approval. Financial values are estimates, not guaranteed revenue."
        )

        if intent.intent == ChatIntent.CUSTOMER_RISK_EXPLANATION:
            risk = payloads.get("get_chat_customer_risk_explanation")
            summary = payloads.get("get_chat_customer_summary")
            if risk is None:
                return "I need a customer ID to explain urgency."
            lines = [
                f"{risk.customer_id} has priority score {risk.priority_score} "
                f"with decision {risk.decision}.",
                f"Primary signal: {risk.primary_signal or 'elevated churn indicators'}.",
            ]
            if risk.top_risk_signals:
                lines.append("Key drivers: " + "; ".join(risk.top_risk_signals[:3]) + ".")
            if summary:
                lines.append(f"Suggested RM action: {summary.suggested_action}")
            lines.append(disclaimer)
            return "\n\n".join(lines)

        if intent.intent == ChatIntent.CUSTOMER_ELIGIBILITY_EXPLANATION:
            elig = payloads.get("get_chat_customer_eligibility")
            if elig is None:
                return "Please specify which customer to review for eligibility."
            lines = [f"Eligibility review for {elig.customer_id}:"]
            if elig.rejected_offers:
                for offer in elig.rejected_offers[:3]:
                    reasons = ", ".join(offer.get("reason_codes", []))
                    lines.append(f"- {offer.get('offer_name')} rejected: {reasons}")
            if elig.customer_id == "C004":
                lines.append(
                    "C004 is restricted from new lending offers due to elevated DPD "
                    "and credit distress policy."
                )
                lines.append(
                    "Repayment-support consultation may still be available for discussion."
                )
            if elig.eligible_offers:
                names = ", ".join(o["offer_name"] for o in elig.eligible_offers[:2])
                lines.append(f"Eligible discussion offers include: {names}.")
            lines.append(disclaimer)
            return "\n\n".join(lines)

        if intent.intent == ChatIntent.CUSTOMER_OFFER_EXPLANATION:
            rec = payloads.get("get_chat_customer_recommendation")
            summary = payloads.get("get_chat_customer_summary")
            if rec and rec.has_recommendation:
                return (
                    f"For {rec.customer_id}, the latest recommendation suggests "
                    f"{rec.recommended_offer_name or 'a retention discussion offer'} "
                    f"(status: {rec.status}). {rec.executive_summary}\n\n{disclaimer}"
                )
            if summary:
                return (
                    f"For {summary.customer_id}, consider discussing "
                    f"{summary.recommended_offer_name or 'eligible retention options'}. "
                    f"{summary.suggested_action}\n\n{disclaimer}"
                )
            return "Please specify a customer to review recommended offers."

        if intent.intent == ChatIntent.PRIORITY_CUSTOMER_LIST:
            customers = payloads.get("get_chat_priority_customers", [])
            if "high_value_high_risk" in intent.extracted_terms:
                page = PortfolioService(self.session).list_customers(
                    page=1,
                    page_size=10,
                    minimum_priority=50,
                    sort_by="priority_score",
                    sort_order="desc",
                )
                customers = [
                    chat_tools.ChatPriorityCustomer(
                        customer_id=row.customer_id,
                        full_name=row.full_name,
                        priority_score=row.priority_score,
                        decision=row.decision.value,
                        primary_trigger=row.primary_trigger,
                        suggested_action=row.recommended_action,
                        revenue_at_risk=row.revenue_at_risk,
                    )
                    for row in page.items
                    if (
                        row.churn_score > CHURN_BAND_HIGH_MAX
                        and row.value_score > CHURN_BAND_HIGH_MAX
                    )
                ]
            if not customers:
                return "No customers currently require urgent RM outreach."
            lines = ["Priority customers to contact:"]
            for item in customers[: intent.requested_limit or 10]:
                lines.append(
                    f"- {item.customer_id} ({item.full_name}): priority {item.priority_score}, "
                    f"{item.decision}. Signal: {item.primary_trigger or 'multiple'}. "
                    f"Revenue at risk (estimate): {_format_inr(item.revenue_at_risk)}."
                )
            lines.append(
                "Customers with NO_ACTION are excluded from urgent call lists."
            )
            return "\n".join(lines)

        if intent.intent == ChatIntent.TRIGGER_SEARCH:
            matches = payloads.get("search_customers_by_trigger", [])
            if not matches:
                return f"No customers found for trigger type {intent.trigger_type}."
            trigger_label = intent.trigger_type.replace("_", " ").lower()
            lines = [f"Customers with recent {trigger_label} signals:"]
            for match in matches[:10]:
                lines.append(
                    f"- {match.customer_id}: {match.trigger_type} ({match.severity}), "
                    f"priority {match.priority_score}, decision {match.decision}"
                )
            return "\n".join(lines)

        if intent.intent == ChatIntent.REVENUE_AT_RISK:
            portfolio = payloads.get("get_chat_portfolio_summary")
            if portfolio is None:
                return "Portfolio revenue data is unavailable."
            return (
                f"Total estimated revenue at risk across the portfolio is "
                f"{_format_inr(portfolio.total_revenue_at_risk)}. "
                "This is an estimate based on synthetic churn probability and annual value — "
                "not guaranteed loss."
            )

        if intent.intent == ChatIntent.PORTFOLIO_SUMMARY:
            portfolio = payloads.get("get_chat_portfolio_summary")
            if portfolio is None:
                return "Portfolio summary is unavailable."
            return (
                f"Portfolio covers {portfolio.total_customers} customers: "
                f"{portfolio.retain_count} RETAIN, {portfolio.review_count} REVIEW, "
                f"{portfolio.monitor_count} MONITOR, {portfolio.no_action_count} NO_ACTION. "
                f"Estimated revenue at risk: {_format_inr(portfolio.total_revenue_at_risk)}. "
                f"Open alerts: {portfolio.open_alerts}."
            )

        if intent.intent == ChatIntent.CUSTOMER_COMPARISON:
            rows = payloads.get("compare_customers", [])
            if not rows:
                return "Provide two to five customer IDs to compare, e.g. 'Compare C001 and C008'."
            lines = ["Customer comparison:"]
            for row in rows:
                lines.append(
                    f"- {row.customer_id} ({row.full_name}): priority {row.priority_score}, "
                    f"churn {row.churn_score}, value {row.value_score}, decision {row.decision}, "
                    f"revenue at risk {_format_inr(row.revenue_at_risk)}"
                )
            return "\n".join(lines)

        if intent.intent == ChatIntent.RM_TALKING_POINTS:
            points = payloads.get("get_rm_talking_points")
            if points is None:
                return "Specify a customer ID for talking points."
            bullets = "\n".join(f"- {point}" for point in points.talking_points[:5])
            return f"{points.executive_summary}\n\nTalking points:\n{bullets}\n\n{disclaimer}"

        if intent.intent == ChatIntent.RECOMMENDATION_STATUS:
            rec = payloads.get("get_recommendation_status")
            if rec is None:
                return "Specify a customer to check recommendation status."
            if not rec.has_recommendation:
                return f"No persisted recommendation found for {rec.customer_id}."
            return (
                f"{rec.customer_id} recommendation status: {rec.status}. "
                f"Decision: {rec.decision}. Offer: {rec.recommended_offer_name or 'none'}. "
                f"Expected net benefit (estimate): "
                f"{_format_inr(rec.expected_net_benefit or 0)}."
            )

        if intent.intent == ChatIntent.DATA_FRESHNESS:
            if intent.customer_ids:
                fresh = payloads.get("get_customer_data_freshness")
                if fresh is None:
                    return "Customer freshness data unavailable."
                stale = ", ".join(fresh.stale_sources) or "none"
                return (
                    f"{fresh.customer_id} data freshness — stale or missing sources: {stale}. "
                    f"Warnings: {'; '.join(fresh.data_warnings) or 'none'}."
                )
            stale_customers = payloads.get("get_customers_with_stale_data", [])
            if not stale_customers:
                return "No customers currently flagged with stale data sources."
            lines = ["Customers with stale or missing data:"]
            for row in stale_customers[:10]:
                lines.append(
                    f"- {row.customer_id} ({row.full_name}): {', '.join(row.stale_sources)}"
                )
            return "\n".join(lines)

        if intent.intent == ChatIntent.DPD_EXPLANATION:
            elig = payloads.get("get_chat_customer_eligibility")
            risk = payloads.get("get_chat_customer_risk_explanation")
            customer = intent.customer_ids[0] if intent.customer_ids else "the customer"
            lines = [
                f"DPD (days past due) is a key credit-health signal for {customer}.",
            ]
            if risk:
                lines.append(
                    f"Current priority score is {risk.priority_score} "
                    f"with decision {risk.decision}."
                )
            if customer == "C004":
                lines.append(
                    "C004 shows elevated DPD (60 days), which triggers lending restrictions "
                    "and prioritizes repayment-support consultation."
                )
                rejected_lending = [
                    offer
                    for offer in (elig.rejected_offers if elig else [])
                    if offer.get("offer_id") in C004_RESTRICTED_LENDING_OFFER_IDS
                ]
                if rejected_lending:
                    lines.append("Home-loan and card lending offers are blocked by policy.")
            lines.append(disclaimer)
            return "\n\n".join(lines)

        if intent.intent == ChatIntent.FOLLOW_UP_QUESTION:
            summary = payloads.get("get_chat_customer_summary")
            rec = payloads.get("get_chat_customer_recommendation")
            if summary:
                offer = summary.recommended_offer_name or "eligible discussion options"
                return (
                    f"For {summary.customer_id}, next step: {summary.suggested_action} "
                    f"Consider discussing {offer}. Priority score: {summary.priority_score}.\n\n"
                    f"{disclaimer}"
                )
            if rec and rec.has_recommendation:
                return (
                    f"Follow up on {rec.customer_id}'s recommendation (status {rec.status}): "
                    f"{rec.executive_summary}\n\n{disclaimer}"
                )
            return (
                "Please specify which customer you are following up on, "
                "or ask about portfolio priorities."
            )

        return "I could not generate a response for that request."

    def _conversation_title(self, intent: IntentDetectionResult, customer_ids: list[str]) -> str:
        if customer_ids:
            return f"{customer_ids[0]} Retention Review"
        if intent.intent == ChatIntent.CUSTOMER_COMPARISON:
            return "Customer Comparison"
        if intent.intent in {ChatIntent.PRIORITY_CUSTOMER_LIST, ChatIntent.PORTFOLIO_SUMMARY}:
            return "Priority Customer Review"
        if intent.intent == ChatIntent.TRIGGER_SEARCH:
            return "Trigger Search"
        return "RM Copilot Chat"

    def _clarification_response(
        self,
        conversation,
        context: ChatContext,
        request: ChatRequest,
        *,
        question: str | None = None,
    ) -> ChatResponse:
        answer = question or context.clarification_question or "Please clarify your request."
        if self.settings.chat_history_enabled:
            self.repository.add_message(
                conversation_id=conversation.id,
                role=ChatMessageRole.USER,
                content=request.message,
                customer_ids=context.customer_ids,
            )
            assistant = self.repository.add_message(
                conversation_id=conversation.id,
                role=ChatMessageRole.ASSISTANT,
                content=answer,
                warnings=context.context_warnings,
            )
            message_id = assistant.id
        else:
            message_id = conversation.id
        return ChatResponse(
            conversation_id=conversation.id,
            message_id=message_id,
            answer=answer,
            intent=ChatIntent.FOLLOW_UP_QUESTION,
            customer_ids=context.customer_ids,
            used_tools=[],
            evidence=[],
            warnings=context.context_warnings,
            suggested_questions=["Why is C001 urgent?", "Who should I call today?"],
            generated_at=_utc_now(),
            mode=LLMMode.MOCK if self.settings.mock_llm_mode else LLMMode.QWEN,
        )

    def _unsupported_response(
        self, conversation, intent: IntentDetectionResult, request: ChatRequest
    ) -> ChatResponse:
        answer = intent.unsupported_reason or (
            "That request is outside supported RM retention functionality."
        )
        if self.settings.chat_history_enabled:
            self.repository.add_message(
                conversation_id=conversation.id,
                role=ChatMessageRole.USER,
                content=request.message,
            )
            assistant = self.repository.add_message(
                conversation_id=conversation.id,
                role=ChatMessageRole.ASSISTANT,
                content=answer,
            )
            message_id = assistant.id
        else:
            message_id = conversation.id
        return ChatResponse(
            conversation_id=conversation.id,
            message_id=message_id,
            answer=answer,
            intent=ChatIntent.UNSUPPORTED,
            customer_ids=intent.customer_ids,
            used_tools=[],
            evidence=[],
            warnings=[],
            suggested_questions=suggested_questions(ChatIntent.GENERAL_HELP, []),
            generated_at=_utc_now(),
            mode=LLMMode.MOCK if self.settings.mock_llm_mode else LLMMode.QWEN,
        )
