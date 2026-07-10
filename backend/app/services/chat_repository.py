"""Chat conversation and message persistence."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from sqlmodel import Session, select

from app.core.config import Settings, get_settings
from app.core.exceptions import ChatConversationNotFoundError
from app.models.chat_conversation import ChatConversation
from app.models.chat_message import ChatMessage
from app.models.enums import ChatConversationStatus, ChatMessageRole
from app.schemas.chat import ChatEvidence, ChatMessageResponse, ConversationSummary
from app.schemas.common import PaginatedResponse
from app.services.repository_utils import count_query, paginate_offset, validate_pagination

SortOrder = Literal["asc", "desc"]


class ChatRepository:
    """Data access for RM chat conversations."""

    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self.session = session
        self.settings = settings or get_settings()

    def create_conversation(
        self,
        *,
        rm_id: str,
        title: str | None,
        active_customer_id: str | None,
        expires_at: datetime | None,
    ) -> ChatConversation:
        conversation = ChatConversation(
            rm_id=rm_id,
            title=title,
            active_customer_id=active_customer_id,
            expires_at=expires_at,
            status=ChatConversationStatus.ACTIVE,
        )
        self.session.add(conversation)
        self.session.flush()
        return conversation

    def get_conversation(self, conversation_id: str) -> ChatConversation:
        conversation = self.session.get(ChatConversation, conversation_id)
        if conversation is None:
            raise ChatConversationNotFoundError(
                message=f"Conversation {conversation_id} was not found",
            )
        return conversation

    def close_conversation(self, conversation: ChatConversation) -> ChatConversation:
        conversation.status = ChatConversationStatus.CLOSED
        self.session.add(conversation)
        self.session.flush()
        return conversation

    def update_active_customer(
        self, conversation: ChatConversation, customer_id: str | None
    ) -> None:
        conversation.active_customer_id = customer_id
        self.session.add(conversation)
        self.session.flush()

    def update_title(self, conversation: ChatConversation, title: str) -> None:
        conversation.title = title
        self.session.add(conversation)
        self.session.flush()

    def add_message(
        self,
        *,
        conversation_id: str,
        role: ChatMessageRole,
        content: str,
        customer_ids: list[str] | None = None,
        used_tools: list[str] | None = None,
        evidence: list[ChatEvidence] | None = None,
        warnings: list[str] | None = None,
    ) -> ChatMessage:
        message = ChatMessage(
            conversation_id=conversation_id,
            role=role,
            content=content[:4096],
            customer_ids_json=list(customer_ids or []),
            used_tools_json=list(used_tools or []),
            evidence_json=[item.model_dump(mode="json") for item in (evidence or [])],
            warnings_json=list(warnings or []),
        )
        self.session.add(message)
        conversation = self.get_conversation(conversation_id)
        conversation.updated_at = message.created_at
        self.session.add(conversation)
        self.session.flush()
        return message

    def list_recent_messages(
        self, conversation_id: str, *, limit: int
    ) -> list[ChatMessageResponse]:
        statement = (
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        messages = list(reversed(self.session.exec(statement).all()))
        return [self._to_message_response(message) for message in messages]

    def list_conversations(
        self,
        *,
        rm_id: str,
        page: int = 1,
        page_size: int = 20,
        status: ChatConversationStatus | None = None,
        sort_order: SortOrder = "desc",
    ) -> PaginatedResponse[ConversationSummary]:
        validate_pagination(page, page_size)
        statement = select(ChatConversation).where(ChatConversation.rm_id == rm_id)
        if status is not None:
            statement = statement.where(ChatConversation.status == status)
        order = (
            ChatConversation.updated_at.desc()
            if sort_order == "desc"
            else ChatConversation.updated_at.asc()
        )
        statement = statement.order_by(order)
        total = count_query(self.session, statement)
        conversations = self.session.exec(
            statement.offset(paginate_offset(page, page_size)).limit(page_size)
        ).all()
        return PaginatedResponse.build(
            items=[self._to_summary(conversation) for conversation in conversations],
            total=total,
            page=page,
            page_size=page_size,
        )

    def count_messages(self, conversation_id: str) -> int:
        statement = select(ChatMessage).where(ChatMessage.conversation_id == conversation_id)
        return count_query(self.session, statement)

    @staticmethod
    def _to_message_response(message: ChatMessage) -> ChatMessageResponse:
        evidence = [ChatEvidence.model_validate(item) for item in message.evidence_json]
        return ChatMessageResponse(
            message_id=message.id,
            role=message.role,
            content=message.content,
            customer_ids=list(message.customer_ids_json or []),
            used_tools=list(message.used_tools_json or []),
            evidence=evidence,
            warnings=list(message.warnings_json or []),
            created_at=message.created_at,
        )

    def _to_summary(self, conversation: ChatConversation) -> ConversationSummary:
        statement = (
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation.id)
            .order_by(ChatMessage.created_at.desc())
            .limit(1)
        )
        last_message = self.session.exec(statement).first()
        preview = last_message.content[:120] if last_message else None
        return ConversationSummary(
            conversation_id=conversation.id,
            title=conversation.title,
            active_customer_id=conversation.active_customer_id,
            last_message_preview=preview,
            message_count=self.count_messages(conversation.id),
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            status=conversation.status,
        )
