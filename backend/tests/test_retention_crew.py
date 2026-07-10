"""Retention crew tests."""

import pytest

from app.core.config import Settings
from app.core.exceptions import AgentExecutionError
from app.crews.retention_crew import RetentionCrew
from app.models.enums import RecommendationDecision


@pytest.fixture
def crew_settings() -> Settings:
    return Settings(app_name="RetainAI", app_env="development", mock_llm_mode=True)


def test_sequential_task_order(crew_settings: Settings, agent_seeded_session):
    crew = RetentionCrew(crew_settings)
    result = crew.kickoff(execution_id="exec-test", customer_id="C001")
    assert result.investigation.customer_id == "C001"
    assert result.decision.customer_id == "C001"
    assert result.offer_strategy.customer_id == "C001"
    assert result.rm_brief.customer_id == "C001"
    assert result.execution_metadata.task_count == 4
    assert "signal_investigation" in result.execution_metadata.task_durations_ms


def test_mock_mode_no_network(crew_settings: Settings, agent_seeded_session, monkeypatch):
    def _fail_network(*_args, **_kwargs):
        raise AssertionError("Network call attempted in mock mode")

    monkeypatch.setattr("app.core.llm.create_llm", _fail_network)
    crew = RetentionCrew(crew_settings)
    result = crew.kickoff(execution_id="exec-mock", customer_id="C001")
    assert result.execution_metadata.mode.value == "MOCK"


def test_c001_complete_result(crew_settings: Settings, agent_seeded_session):
    result = RetentionCrew(crew_settings).kickoff(execution_id="exec-c001", customer_id="C001")
    assert result.decision.deterministic_decision == RecommendationDecision.RETAIN
    assert result.offer_strategy.recommended_offer_id is not None
    assert result.rm_brief.executive_summary


def test_c004_policy_safe_result(crew_settings: Settings, agent_seeded_session):
    result = RetentionCrew(crew_settings).kickoff(execution_id="exec-c004", customer_id="C004")
    assert result.offer_strategy.recommended_offer_id not in {"OFFER-HL-FEE", "OFFER-HL-RATE"}
    assert result.decision.policy_warnings or result.offer_strategy.policy_warnings


def test_c008_fd_result(crew_settings: Settings, agent_seeded_session):
    result = RetentionCrew(crew_settings).kickoff(execution_id="exec-c008", customer_id="C008")
    assert result.customer_id == "C008"
    assert result.rm_brief.executive_summary


def test_malformed_output_handled(crew_settings: Settings, agent_seeded_session, monkeypatch):
    def _broken_investigator(*_args, **_kwargs):
        raise ValueError("Malformed LLM JSON")

    monkeypatch.setattr("app.crews.retention_crew.run_signal_investigator", _broken_investigator)
    crew = RetentionCrew(crew_settings)
    with pytest.raises(AgentExecutionError):
        crew.kickoff(execution_id="exec-bad", customer_id="C001")
