"""Chat intent detection tests."""

import pytest

from app.models.enums import ChatIntent
from app.services.chat_intent_service import ChatIntentService


@pytest.fixture
def intent_service() -> ChatIntentService:
    return ChatIntentService()


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("Why is C001 urgent?", ChatIntent.CUSTOMER_RISK_EXPLANATION),
        ("Why is C004 not eligible for a loan?", ChatIntent.CUSTOMER_ELIGIBILITY_EXPLANATION),
        ("Who should I call today?", ChatIntent.PRIORITY_CUSTOMER_LIST),
        ("Which customers have recent home-loan inquiries?", ChatIntent.TRIGGER_SEARCH),
        ("What offer is recommended for C008?", ChatIntent.CUSTOMER_OFFER_EXPLANATION),
        ("Compare C001 and C008.", ChatIntent.CUSTOMER_COMPARISON),
        ("How much revenue is currently at risk?", ChatIntent.REVENUE_AT_RISK),
        ("Draft talking points for C003.", ChatIntent.RM_TALKING_POINTS),
        ("Show high-value, high-risk customers.", ChatIntent.PRIORITY_CUSTOMER_LIST),
        ("What is the status of C001's latest recommendation?", ChatIntent.RECOMMENDATION_STATUS),
        ("Which customers have stale data?", ChatIntent.DATA_FRESHNESS),
        ("Why is DPD important for C004?", ChatIntent.DPD_EXPLANATION),
        ("What should I do next for C007?", ChatIntent.FOLLOW_UP_QUESTION),
        ("What can you help with?", ChatIntent.GENERAL_HELP),
        ("Delete all customers from database", ChatIntent.UNSUPPORTED),
    ],
)
def test_intent_detection(intent_service: ChatIntentService, message: str, expected: ChatIntent):
    result = intent_service.detect(message)
    assert result.intent == expected


def test_customer_id_extraction(intent_service: ChatIntentService):
    result = intent_service.detect("Compare C001 and C008 for retention")
    assert result.customer_ids == ["C001", "C008"]


def test_trigger_extraction(intent_service: ChatIntentService):
    result = intent_service.detect("Which customers have salary stopped recently?")
    assert result.trigger_type == "SALARY_STOPPED"


def test_follow_up_with_active_customer(intent_service: ChatIntentService):
    result = intent_service.detect("What offer should I discuss?", has_active_customer=True)
    assert result.intent == ChatIntent.CUSTOMER_OFFER_EXPLANATION
