"""Chat context resolution tests."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlmodel import Session

from app.core.config import Settings
from app.core.exceptions import ChatConversationClosedError
from app.models.enums import ChatMessageRole
from app.services.chat_context_service import ChatContextService
from app.services.chat_repository import ChatRepository


@pytest.fixture
def chat_settings() -> Settings:
    return Settings(
        app_name="RetainAI",
        app_env="development",
        mock_llm_mode=True,
        chat_history_enabled=True,
        chat_max_history_messages=3,
        chat_conversation_ttl_hours=24,
    )


def test_explicit_customer_overrides_context(
    agent_seeded_session: Session, chat_settings: Settings
):
    repo = ChatRepository(agent_seeded_session, chat_settings)
    conversation = repo.create_conversation(
        rm_id="RM-01",
        title=None,
        active_customer_id="C001",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    service = ChatContextService(agent_seeded_session, chat_settings)
    context = service.resolve(
        conversation=conversation,
        explicit_customer_id="C008",
        include_history=True,
    )
    assert context.active_customer_id == "C008"


def test_follow_up_reuses_active_customer(agent_seeded_session: Session, chat_settings: Settings):
    repo = ChatRepository(agent_seeded_session, chat_settings)
    conversation = repo.create_conversation(
        rm_id="RM-01",
        title=None,
        active_customer_id="C001",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    repo.add_message(
        conversation_id=conversation.id,
        role=ChatMessageRole.USER,
        content="Why is C001 urgent?",
        customer_ids=["C001"],
    )
    service = ChatContextService(agent_seeded_session, chat_settings)
    context = service.resolve(
        conversation=conversation,
        explicit_customer_id=None,
        include_history=True,
    )
    assert context.active_customer_id == "C001"
    assert len(context.recent_messages) <= chat_settings.chat_max_history_messages


def test_multiple_customer_ambiguity(agent_seeded_session: Session, chat_settings: Settings):
    repo = ChatRepository(agent_seeded_session, chat_settings)
    conversation = repo.create_conversation(
        rm_id="RM-01",
        title=None,
        active_customer_id=None,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    repo.add_message(
        conversation_id=conversation.id,
        role=ChatMessageRole.USER,
        content="Tell me about C001",
        customer_ids=["C001"],
    )
    repo.add_message(
        conversation_id=conversation.id,
        role=ChatMessageRole.USER,
        content="Tell me about C008",
        customer_ids=["C008"],
    )
    service = ChatContextService(agent_seeded_session, chat_settings)
    context = service.resolve(
        conversation=conversation,
        explicit_customer_id=None,
        include_history=True,
    )
    assert context.ambiguous is True
    assert context.clarification_question


def test_closed_conversation_rejected(agent_seeded_session: Session, chat_settings: Settings):
    repo = ChatRepository(agent_seeded_session, chat_settings)
    conversation = repo.create_conversation(
        rm_id="RM-01",
        title=None,
        active_customer_id=None,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    repo.close_conversation(conversation)
    service = ChatContextService(agent_seeded_session, chat_settings)
    with pytest.raises(ChatConversationClosedError):
        service.resolve(
            conversation=conversation,
            explicit_customer_id=None,
            include_history=True,
        )


def test_expired_conversation_rejected(agent_seeded_session: Session, chat_settings: Settings):
    repo = ChatRepository(agent_seeded_session, chat_settings)
    conversation = repo.create_conversation(
        rm_id="RM-01",
        title=None,
        active_customer_id=None,
        expires_at=datetime.now(UTC) - timedelta(hours=1),
    )
    service = ChatContextService(agent_seeded_session, chat_settings)
    with pytest.raises(ChatConversationClosedError):
        service.resolve(
            conversation=conversation,
            explicit_customer_id=None,
            include_history=True,
        )
