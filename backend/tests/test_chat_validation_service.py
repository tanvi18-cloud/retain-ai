"""Chat validation service tests."""


import pytest

from app.models.enums import ChatIntent
from app.schemas.chat import ChatEvidence, RMChatAgentOutput
from app.services.chat_validation_service import ChatValidationService


@pytest.fixture
def validator(agent_seeded_session) -> ChatValidationService:
    return ChatValidationService(agent_seeded_session)


def _output(**kwargs) -> RMChatAgentOutput:
    defaults = {
        "answer": "Safe answer with estimates only.",
        "intent": ChatIntent.CUSTOMER_RISK_EXPLANATION,
        "customer_ids": ["C001"],
        "used_tools": ["get_chat_customer_summary"],
        "evidence": [
            ChatEvidence(
                source_system="CORE_BANKING",
                source_type="priority_score",
                customer_id="C001",
                field="priority_score",
                value_summary="84",
            )
        ],
        "warnings": [],
        "suggested_questions": [],
        "confidence": 0.9,
    }
    defaults.update(kwargs)
    return RMChatAgentOutput(**defaults)


def test_valid_output_accepted(validator: ChatValidationService):
    result = validator.validate_output(_output())
    assert result.valid is True


def test_invented_customer_rejected(validator: ChatValidationService):
    result = validator.validate_output(_output(customer_ids=["C999"]))
    assert result.valid is False


def test_invalid_tool_rejected(validator: ChatValidationService):
    result = validator.validate_output(_output(used_tools=["run_sql_query"]))
    assert result.valid is False


def test_approval_claim_rejected(validator: ChatValidationService):
    result = validator.validate_output(
        _output(answer="The loan is pre-approved for this customer.")
    )
    assert result.valid is False


def test_account_number_blocked(validator: ChatValidationService):
    result = validator.validate_output(_output(answer="Account 12345678901234 shows risk."))
    assert result.valid is False


def test_disclaimer_appended(validator: ChatValidationService):
    result = validator.validate_output(
        _output(answer="Consider the home-loan fee waiver offer for discussion.")
    )
    assert result.corrected is True
    assert result.corrected_answer


def test_c004_lending_offer_rejected(validator: ChatValidationService):
    result = validator.validate_output(
        _output(
            customer_ids=["C004"],
            answer="Recommend OFFER-HL-FEE for C004.",
        )
    )
    assert result.valid is False
