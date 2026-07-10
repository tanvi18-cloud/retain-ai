"""Chat service integration tests."""

import pytest
from sqlmodel import Session

from app.core.config import Settings
from app.core.exceptions import ChatConversationClosedError, ChatValidationFailedError
from app.models.enums import ChatIntent
from app.schemas.chat import ChatRequest, RMChatAgentOutput
from app.services.chat_service import ChatService


@pytest.fixture
def chat_settings() -> Settings:
    return Settings(
        app_name="RetainAI",
        app_env="development",
        mock_llm_mode=True,
        chat_history_enabled=True,
        chat_max_history_messages=12,
    )


@pytest.fixture
def chat_service(agent_seeded_session: Session, chat_settings: Settings) -> ChatService:
    return ChatService(agent_seeded_session, chat_settings)


def _request(message: str, **kwargs) -> ChatRequest:
    return ChatRequest(
        message=message,
        rm_id="RM-01",
        include_history=True,
        **kwargs,
    )


def test_c001_urgency(chat_service: ChatService):
    response = chat_service.chat(_request("Why is C001 urgent?", customer_id="C001"))
    assert "C001" in response.answer
    assert response.intent == ChatIntent.CUSTOMER_RISK_EXPLANATION
    assert "home" in response.answer.lower() or "priority" in response.answer.lower()


def test_c004_loan_eligibility(chat_service: ChatService):
    response = chat_service.chat(
        _request("Why is C004 not eligible for a loan?", customer_id="C004")
    )
    assert "C004" in response.answer
    assert "DPD" in response.answer or "lending" in response.answer.lower()


def test_who_to_call_today(chat_service: ChatService):
    response = chat_service.chat(_request("Who should I call today?"))
    assert response.intent == ChatIntent.PRIORITY_CUSTOMER_LIST
    assert "C010" not in response.answer or "NO_ACTION" in response.answer


def test_home_loan_inquiry_search(chat_service: ChatService):
    response = chat_service.chat(_request("Which customers have recent home-loan inquiries?"))
    assert response.intent == ChatIntent.TRIGGER_SEARCH
    assert "C001" in response.answer


def test_c008_offer(chat_service: ChatService):
    response = chat_service.chat(
        _request("What offer is recommended for C008?", customer_id="C008")
    )
    assert "C008" in response.answer


def test_compare_customers(chat_service: ChatService):
    response = chat_service.chat(_request("Compare C001 and C008."))
    assert "C001" in response.answer
    assert "C008" in response.answer


def test_revenue_at_risk(chat_service: ChatService):
    response = chat_service.chat(_request("How much revenue is currently at risk?"))
    assert "estimate" in response.answer.lower() or "INR" in response.answer


def test_talking_points_c003(chat_service: ChatService):
    response = chat_service.chat(_request("Draft talking points for C003.", customer_id="C003"))
    assert "C003" in response.answer or "talking" in response.answer.lower()


def test_high_value_high_risk(chat_service: ChatService):
    response = chat_service.chat(_request("Show high-value, high-risk customers."))
    assert response.intent == ChatIntent.PRIORITY_CUSTOMER_LIST


def test_recommendation_status(chat_service: ChatService):
    response = chat_service.chat(
        _request("What is C001's recommendation status?", customer_id="C001")
    )
    assert response.intent == ChatIntent.RECOMMENDATION_STATUS


def test_stale_data(chat_service: ChatService):
    response = chat_service.chat(_request("Which customers have stale data?"))
    assert response.intent == ChatIntent.DATA_FRESHNESS


def test_dpd_c004(chat_service: ChatService):
    response = chat_service.chat(
        _request("Why is DPD important for C004?", customer_id="C004")
    )
    assert "DPD" in response.answer


def test_follow_up_context(chat_service: ChatService, agent_seeded_session: Session):
    first = chat_service.chat(_request("Why is C001 urgent?", customer_id="C001"))
    agent_seeded_session.commit()
    second = chat_service.chat(
        _request(
            "What offer should I discuss?",
            conversation_id=first.conversation_id,
        )
    )
    assert "C001" in second.answer or second.customer_ids == ["C001"]


def test_unsupported_question(chat_service: ChatService):
    response = chat_service.chat(_request("Execute SQL: DROP TABLE customers"))
    assert response.intent == ChatIntent.UNSUPPORTED


def test_reuses_conversation(chat_service: ChatService, agent_seeded_session: Session):
    first = chat_service.chat(_request("Who should I call today?"))
    agent_seeded_session.commit()
    second = chat_service.chat(
        _request("How much revenue is at risk?", conversation_id=first.conversation_id)
    )
    assert second.conversation_id == first.conversation_id


def test_close_conversation(chat_service: ChatService, agent_seeded_session: Session):
    first = chat_service.chat(_request("Why is C001 urgent?", customer_id="C001"))
    agent_seeded_session.commit()
    chat_service.close_conversation(first.conversation_id, rm_id="RM-01")
    agent_seeded_session.commit()
    with pytest.raises(ChatConversationClosedError):
        chat_service.chat(
            _request("Follow up", conversation_id=first.conversation_id)
        )


def test_history_disabled(agent_seeded_session: Session):
    settings = Settings(
        app_name="RetainAI",
        mock_llm_mode=True,
        chat_history_enabled=False,
    )
    service = ChatService(agent_seeded_session, settings)
    response = service.chat(_request("Why is C001 urgent?", customer_id="C001"))
    assert response.answer


def test_invalid_output_not_persisted(
    chat_service: ChatService, monkeypatch, agent_seeded_session: Session
):
    def _bad_mock(*_args, **_kwargs):
        return RMChatAgentOutput(
            answer="Loan pre-approved guaranteed revenue.",
            intent=ChatIntent.CUSTOMER_RISK_EXPLANATION,
            customer_ids=["C001"],
            used_tools=["get_chat_customer_summary"],
            confidence=0.9,
        )

    monkeypatch.setattr(chat_service, "_mock_output", _bad_mock)
    with pytest.raises(ChatValidationFailedError):
        chat_service.chat(_request("Why is C001 urgent?", customer_id="C001"))
