"""Tests for Offer Strategy agent."""

from app.agents.offer_strategy_agent import run_offer_strategy
from app.core.agent_policy import AGENT_ELIGIBILITY_DISCLAIMER
from app.core.policy_rules import C004_RESTRICTED_LENDING_OFFER_IDS


def test_c001_eligible_home_loan_offer(agent_seeded_engine, agent_settings):
    output = run_offer_strategy("C001", settings=agent_settings)
    assert output.recommended_offer_id in {"OFFER-HL-FEE", "OFFER-HL-RATE"}


def test_c004_no_lending_offer(agent_seeded_engine, agent_settings):
    output = run_offer_strategy("C004", settings=agent_settings)
    if output.recommended_offer_id:
        assert output.recommended_offer_id not in C004_RESTRICTED_LENDING_OFFER_IDS


def test_c007_travel_card_offer(agent_seeded_engine, agent_settings):
    output = run_offer_strategy("C007", settings=agent_settings)
    assert output.recommended_offer_id == "OFFER-TC-UPGRADE"


def test_c008_fd_renewal_offer(agent_seeded_engine, agent_settings):
    output = run_offer_strategy("C008", settings=agent_settings)
    assert output.recommended_offer_id == "OFFER-FD-RENEW"


def test_disclaimer_present(agent_seeded_engine, agent_settings):
    output = run_offer_strategy("C001", settings=agent_settings)
    assert AGENT_ELIGIBILITY_DISCLAIMER.lower() in output.eligibility_disclaimer.lower()


def test_unknown_offer_rejected_by_validation(agent_seeded_engine, agent_settings):
    from app.schemas.agent_outputs import OfferStrategyOutput
    from app.services.agent_validation_service import AgentValidationService

    output = OfferStrategyOutput(
        customer_id="C001",
        recommended_offer_id="OFFER-UNKNOWN",
        offer_rationale="Test",
        scenario_fit="Test",
        eligibility_disclaimer=AGENT_ELIGIBILITY_DISCLAIMER,
        policy_warnings=[],
        confidence=0.8,
    )
    result = AgentValidationService(agent_settings).validate_offer_strategy("C001", output)
    assert not result.valid
