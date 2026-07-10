"""RM chat agent tests."""

import pytest

from app.core.config import Settings
from app.models.enums import ChatIntent
from app.schemas.chat import ChatContext
from app.services.chat_intent_service import ChatIntentService


@pytest.fixture
def chat_settings() -> Settings:
    return Settings(app_name="RetainAI", mock_llm_mode=True)


def test_mock_mode_uses_deterministic_flow(agent_seeded_session, chat_settings: Settings):
    from app.schemas.chat import ChatRequest
    from app.services.chat_service import ChatService

    service = ChatService(agent_seeded_session, chat_settings)
    response = service.chat(
        ChatRequest(
            message="Why is C001 urgent?",
            rm_id="RM-01",
            customer_id="C001",
        )
    )
    assert response.mode.value == "MOCK"
    assert response.used_tools


def test_qwen_agent_structure(chat_settings: Settings, agent_seeded_session, monkeypatch):
    from app.agents.rm_chat_agent import run_rm_chat_agent
    from app.schemas.chat import RMChatAgentOutput

    intent = ChatIntentService().detect("Why is C001 urgent?")
    context = ChatContext(
        conversation_id="conv-test",
        active_customer_id="C001",
        customer_ids=["C001"],
    )

    def _fake_execute(**_kwargs):
        return RMChatAgentOutput(
            answer="C001 requires urgent review based on tool data.",
            intent=ChatIntent.CUSTOMER_RISK_EXPLANATION,
            customer_ids=["C001"],
            used_tools=["get_chat_customer_risk_explanation"],
            confidence=0.88,
            suggested_questions=["Which offers are eligible?"],
        )

    monkeypatch.setattr(
        "app.agents.rm_chat_agent.execute_structured_task",
        _fake_execute,
    )
    qwen_settings = chat_settings.model_copy(update={"mock_llm_mode": False})
    output = run_rm_chat_agent(
        message="Why is C001 urgent?",
        intent=intent,
        context=context,
        settings=qwen_settings,
        session=agent_seeded_session,
    )
    assert output.answer
    assert output.customer_ids == ["C001"]
