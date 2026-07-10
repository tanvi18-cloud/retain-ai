"""Tests for deterministic mock LLM service."""

import pytest

from app.core.policy_rules import C004_RESTRICTED_LENDING_OFFER_IDS
from app.models.enums import RecommendationDecision
from app.services.mock_llm_service import MockLLMService


@pytest.mark.parametrize(
    "customer_id",
    ["C001", "C002", "C003", "C004", "C005", "C006", "C007", "C008", "C009", "C010"],
)
def test_mock_service_all_customer_scenarios(agent_seeded_engine, agent_settings, customer_id):
    service = MockLLMService(agent_settings)
    investigation = service.signal_investigation(customer_id)
    decision = service.retention_decision(customer_id, investigation)
    offer = service.offer_strategy(customer_id, investigation, decision)
    brief = service.rm_copilot_brief(customer_id, investigation, decision, offer)

    assert investigation.customer_id == customer_id
    assert decision.customer_id == customer_id
    assert offer.customer_id == customer_id
    assert brief.customer_id == customer_id


def test_c001_home_loan_urgency(agent_seeded_engine, agent_settings):
    service = MockLLMService(agent_settings)
    investigation = service.signal_investigation("C001")
    decision = service.retention_decision("C001", investigation)

    assert "home-loan" in investigation.primary_signal.lower()
    assert decision.deterministic_decision == RecommendationDecision.RETAIN
    assert decision.urgency.value in {"IMMEDIATE", "WITHIN_24_HOURS"}


def test_c004_lending_restriction(agent_seeded_engine, agent_settings):
    service = MockLLMService(agent_settings)
    offer = service.offer_strategy("C004")
    if offer.recommended_offer_id:
        assert offer.recommended_offer_id not in C004_RESTRICTED_LENDING_OFFER_IDS
    assert (
        any(
            "restricted" in warning.lower() or "DPD" in warning for warning in offer.policy_warnings
        )
        or offer.recommended_offer_id == "OFFER-REPAY-SUPPORT"
    )


def test_c010_no_action(agent_seeded_engine, agent_settings):
    service = MockLLMService(agent_settings)
    decision = service.retention_decision("C010")
    offer = service.offer_strategy("C010")

    assert decision.deterministic_decision == RecommendationDecision.NO_ACTION
    assert offer.recommended_offer_id is None


def test_mock_uses_actual_eligible_offer_ids(agent_seeded_engine, agent_settings):
    service = MockLLMService(agent_settings)
    offer = service.offer_strategy("C001")
    assert offer.recommended_offer_id in {"OFFER-HL-FEE", "OFFER-HL-RATE", None}


def test_mock_outputs_are_deterministic(agent_seeded_engine, agent_settings):
    service = MockLLMService(agent_settings)
    first = service.signal_investigation("C003")
    second = service.signal_investigation("C003")
    assert first.primary_signal == second.primary_signal
    assert first.confidence == second.confidence
