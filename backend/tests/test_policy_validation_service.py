"""Final policy validation tests."""

import pytest

from app.core.config import Settings
from app.crews.retention_crew import RetentionCrew
from app.models.enums import RecommendationDecision
from app.services.analysis_service import AnalysisService
from app.services.policy_validation_service import PolicyValidationService


@pytest.fixture
def policy_settings() -> Settings:
    return Settings(app_name="RetainAI", app_env="development", mock_llm_mode=True)


def test_valid_result_accepted(policy_settings: Settings, agent_seeded_session):
    analysis = AnalysisService(agent_seeded_session).analyze_customer_rules_only("C001")
    crew_result = RetentionCrew(policy_settings).kickoff(
        execution_id="exec-val", customer_id="C001"
    )
    result = PolicyValidationService(agent_seeded_session, policy_settings).validate_crew_result(
        customer_id="C001",
        analysis=analysis,
        crew_result=crew_result,
    )
    assert result.valid is True


def test_altered_score_rejected(policy_settings: Settings, agent_seeded_session):
    analysis = AnalysisService(agent_seeded_session).analyze_customer_rules_only("C001")
    crew_result = RetentionCrew(policy_settings).kickoff(
        execution_id="exec-alt", customer_id="C001"
    )
    crew_result.decision.deterministic_decision = RecommendationDecision.NO_ACTION
    result = PolicyValidationService(agent_seeded_session, policy_settings).validate_crew_result(
        customer_id="C001",
        analysis=analysis,
        crew_result=crew_result,
    )
    assert result.valid is False


def test_wrong_customer_id_rejected(policy_settings: Settings, agent_seeded_session):
    analysis = AnalysisService(agent_seeded_session).analyze_customer_rules_only("C001")
    crew_result = RetentionCrew(policy_settings).kickoff(
        execution_id="exec-wrong", customer_id="C001"
    )
    crew_result.investigation.customer_id = "C999"
    result = PolicyValidationService(agent_seeded_session, policy_settings).validate_crew_result(
        customer_id="C001",
        analysis=analysis,
        crew_result=crew_result,
    )
    assert result.valid is False
    assert any("mismatch" in error for error in result.errors)


def test_unknown_offer_rejected(policy_settings: Settings, agent_seeded_session):
    analysis = AnalysisService(agent_seeded_session).analyze_customer_rules_only("C001")
    crew_result = RetentionCrew(policy_settings).kickoff(
        execution_id="exec-unknown", customer_id="C001"
    )
    crew_result.offer_strategy.recommended_offer_id = "OFFER-NOT-REAL"
    result = PolicyValidationService(agent_seeded_session, policy_settings).validate_crew_result(
        customer_id="C001",
        analysis=analysis,
        crew_result=crew_result,
    )
    assert result.valid is False


def test_c004_lending_offer_rejected(policy_settings: Settings, agent_seeded_session):
    analysis = AnalysisService(agent_seeded_session).analyze_customer_rules_only("C004")
    crew_result = RetentionCrew(policy_settings).kickoff(
        execution_id="exec-c004", customer_id="C004"
    )
    crew_result.offer_strategy.recommended_offer_id = "OFFER-HL-FEE"
    result = PolicyValidationService(agent_seeded_session, policy_settings).validate_crew_result(
        customer_id="C004",
        analysis=analysis,
        crew_result=crew_result,
    )
    assert result.valid is False


def test_missing_disclaimer_corrected(policy_settings: Settings, agent_seeded_session):
    analysis = AnalysisService(agent_seeded_session).analyze_customer_rules_only("C001")
    crew_result = RetentionCrew(policy_settings).kickoff(
        execution_id="exec-disclaimer", customer_id="C001"
    )
    crew_result.offer_strategy.eligibility_disclaimer = ""
    result = PolicyValidationService(agent_seeded_session, policy_settings).validate_crew_result(
        customer_id="C001",
        analysis=analysis,
        crew_result=crew_result,
    )
    assert "eligibility_disclaimer" in result.corrected_fields or result.warnings


def test_approval_promise_rejected(policy_settings: Settings, agent_seeded_session):
    analysis = AnalysisService(agent_seeded_session).analyze_customer_rules_only("C001")
    crew_result = RetentionCrew(policy_settings).kickoff(
        execution_id="exec-approval", customer_id="C001"
    )
    crew_result.rm_brief.executive_summary = "Credit approved and guaranteed revenue secured."
    result = PolicyValidationService(agent_seeded_session, policy_settings).validate_crew_result(
        customer_id="C001",
        analysis=analysis,
        crew_result=crew_result,
    )
    assert result.valid is False


def test_financial_mismatch_detected(policy_settings: Settings, agent_seeded_session):
    analysis = AnalysisService(agent_seeded_session).analyze_customer_rules_only("C001")
    crew_result = RetentionCrew(policy_settings).kickoff(
        execution_id="exec-fin", customer_id="C001"
    )
    crew_result.offer_strategy.expected_net_benefit = 999999.0
    result = PolicyValidationService(agent_seeded_session, policy_settings).validate_crew_result(
        customer_id="C001",
        analysis=analysis,
        crew_result=crew_result,
    )
    assert result.valid is False
