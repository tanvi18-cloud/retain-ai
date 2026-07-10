"""Tests for agent validation service."""

import pytest

from app.core.agent_policy import AGENT_ELIGIBILITY_DISCLAIMER
from app.core.exceptions import AgentValidationFailedError
from app.models.enums import RecommendationDecision
from app.models.offer import Offer
from app.schemas.agent_outputs import (
    DataQuality,
    OfferStrategyOutput,
    RetentionDecisionOutput,
    SignalInvestigation,
    Urgency,
)
from app.services.agent_validation_service import AgentValidationService
from app.services.mock_llm_service import MockLLMService


def _investigation(customer_id: str) -> SignalInvestigation:
    return SignalInvestigation(
        customer_id=customer_id,
        primary_signal="Test signal",
        primary_signal_source="CRM",
        supporting_signals=[],
        counter_signals=[],
        data_quality=DataQuality.GOOD,
        missing_data=[],
        stale_data_sources=[],
        investigation_summary="Summary",
        evidence_references=[],
        confidence=0.8,
    )


def test_altered_score_rejected(agent_seeded_engine, agent_settings):
    validator = AgentValidationService(agent_settings)
    output = RetentionDecisionOutput(
        customer_id="C001",
        deterministic_decision=RecommendationDecision.NO_ACTION,
        agent_supported_decision=RecommendationDecision.NO_ACTION,
        urgency=Urgency.NONE,
        recommended_contact_window="None",
        business_reason="Test",
        customer_value_context="Test",
        risks=[],
        policy_warnings=[],
        score_consistency_valid=True,
        confidence=0.8,
    )
    result = validator.validate_retention_decision("C001", output)
    assert not result.valid
    assert any("decision" in error.lower() for error in result.errors)


def test_unknown_offer_rejected(agent_seeded_engine, agent_settings):
    validator = AgentValidationService(agent_settings)
    output = OfferStrategyOutput(
        customer_id="C001",
        recommended_offer_id="OFFER-UNKNOWN",
        offer_rationale="Test",
        scenario_fit="Test",
        eligibility_disclaimer=AGENT_ELIGIBILITY_DISCLAIMER,
        policy_warnings=[],
        confidence=0.8,
    )
    result = validator.validate_offer_strategy("C001", output)
    assert not result.valid


def test_c004_lending_offer_rejected(agent_seeded_engine, agent_settings):
    validator = AgentValidationService(agent_settings)
    output = OfferStrategyOutput(
        customer_id="C004",
        recommended_offer_id="OFFER-HL-FEE",
        offer_rationale="Test",
        scenario_fit="Test",
        eligibility_disclaimer=AGENT_ELIGIBILITY_DISCLAIMER,
        policy_warnings=[],
        confidence=0.8,
    )
    result = validator.validate_offer_strategy("C004", output)
    assert not result.valid


def test_financial_mismatch_detected(agent_seeded_engine, agent_settings):
    mock = MockLLMService(agent_settings)
    base = mock.offer_strategy("C001")
    output = base.model_copy(update={"expected_net_benefit": 999999.0})
    result = AgentValidationService(agent_settings).validate_offer_strategy("C001", output)
    assert not result.valid


def test_missing_disclaimer_corrected(agent_seeded_engine, agent_settings):
    mock = MockLLMService(agent_settings)
    base = mock.offer_strategy("C001")
    output = base.model_copy(update={"eligibility_disclaimer": "Short disclaimer"})
    result = AgentValidationService(agent_settings).validate_offer_strategy("C001", output)
    assert result.valid
    assert result.corrected or result.warnings


def test_confidence_validation(agent_seeded_engine, agent_settings):
    output = _investigation("C001").model_copy(update={"confidence": 1.5})
    result = AgentValidationService(agent_settings).validate_signal_investigation("C001", output)
    assert not result.valid


def test_customer_id_mismatch_rejected(agent_seeded_engine, agent_settings):
    output = _investigation("C002")
    result = AgentValidationService(agent_settings).validate_signal_investigation("C001", output)
    assert not result.valid


def test_require_valid_raises(agent_seeded_engine, agent_settings):
    validator = AgentValidationService(agent_settings)
    result = validator.validate_signal_investigation(
        "C001",
        _investigation("C002"),
    )
    with pytest.raises(AgentValidationFailedError):
        validator.require_valid(result)


def test_inactive_offer_rejected(agent_seeded_engine, agent_seeded_session, agent_settings):
    agent_seeded_session.add(
        Offer(
            offer_id="OFFER-INACTIVE-TEST",
            product_type="CREDIT_CARD",
            offer_name="Inactive Test Offer",
            description="Inactive",
            maximum_dpd=30,
            minimum_customer_value=1000.0,
            maximum_offer_cost=100.0,
            estimated_cost=50.0,
            expected_retention_uplift=0.1,
            active=False,
            requires_rm_approval=False,
        )
    )
    agent_seeded_session.commit()
    output = OfferStrategyOutput(
        customer_id="C001",
        recommended_offer_id="OFFER-INACTIVE-TEST",
        offer_rationale="Test",
        scenario_fit="Test",
        eligibility_disclaimer=AGENT_ELIGIBILITY_DISCLAIMER,
        policy_warnings=[],
        confidence=0.8,
    )
    result = AgentValidationService(agent_settings).validate_offer_strategy("C001", output)
    assert not result.valid
