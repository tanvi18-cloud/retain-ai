"""Conversation context resolution for RM chat."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlmodel import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import ChatConversationClosedError
from app.models.chat_conversation import ChatConversation
from app.models.enums import ChatConversationStatus, ChatMessageRole
from app.schemas.chat import VALID_CUSTOMER_IDS, ChatContext, ChatMessageResponse
from app.services.chat_repository import ChatRepository


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class ChatContextService:
    """Resolve active customer and limited conversation history."""

    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.repository = ChatRepository(session, self.settings)

    def resolve(
        self,
        *,
        conversation: ChatConversation,
        explicit_customer_id: str | None,
        include_history: bool,
    ) -> ChatContext:
        """Build chat context from conversation state and request."""
        if conversation.status == ChatConversationStatus.CLOSED:
            raise ChatConversationClosedError(
                message="Conversation is closed and cannot accept new messages",
                details={"conversation_id": conversation.id},
            )
        if conversation.expires_at and _ensure_utc(conversation.expires_at) < _utc_now():
            raise ChatConversationClosedError(
                message="Conversation has expired",
                details={"conversation_id": conversation.id},
            )

        recent_messages: list[ChatMessageResponse] = []
        if include_history and self.settings.chat_history_enabled:
            recent_messages = self.repository.list_recent_messages(
                conversation.id,
                limit=self.settings.chat_max_history_messages,
            )

        discussed_customers = self._customers_from_messages(recent_messages)
        active_customer = explicit_customer_id or conversation.active_customer_id

        if explicit_customer_id:
            active_customer = explicit_customer_id

        ambiguous = False
        clarification = None
        context_warnings: list[str] = []

        if active_customer is None and len(discussed_customers) == 1:
            active_customer = discussed_customers[0]
        elif active_customer is None and len(discussed_customers) > 1:
            ambiguous = True
            clarification = (
                "Which customer should I focus on? Please specify a customer ID "
                f"such as {', '.join(discussed_customers[:3])}."
            )
            context_warnings.append("Multiple customers discussed; customer context is ambiguous.")

        customer_ids = list(discussed_customers)
        if active_customer and active_customer not in customer_ids:
            customer_ids.append(active_customer)

        return ChatContext(
            conversation_id=conversation.id,
            active_customer_id=active_customer,
            customer_ids=customer_ids,
            recent_messages=recent_messages,
            context_warnings=context_warnings,
            ambiguous=ambiguous,
            clarification_question=clarification,
        )

    def get_conversation(
        self,
        conversation_id: str,
        *,
        rm_id: str,
    ) -> ChatConversation:
        """Load an active conversation for an RM."""
        conversation = self.repository.get_conversation(conversation_id)
        if conversation.rm_id != rm_id:
            from app.core.exceptions import ChatAccessDeniedError

            raise ChatAccessDeniedError(
                message="RM is not permitted to access this conversation",
                details={"conversation_id": conversation_id},
            )
        return conversation

    def create_conversation(
        self,
        *,
        rm_id: str,
        active_customer_id: str | None = None,
        title: str | None = None,
    ) -> ChatConversation:
        """Create a new chat conversation."""
        expires_at = _utc_now() + timedelta(hours=self.settings.chat_conversation_ttl_hours)
        return self.repository.create_conversation(
            rm_id=rm_id,
            title=title,
            active_customer_id=active_customer_id,
            expires_at=expires_at,
        )

    @staticmethod
    def _customers_from_messages(messages: list[ChatMessageResponse]) -> list[str]:
        found: list[str] = []
        for message in messages:
            if message.role != ChatMessageRole.USER:
                continue
            for customer_id in message.customer_ids:
                if customer_id in VALID_CUSTOMER_IDS and customer_id not in found:
                    found.append(customer_id)
        return found
