"""Tests for Retention Decision agent."""

from app.agents.retention_decision_agent import run_retention_decision
from app.agents.signal_investigator import run_signal_investigator
from app.models.enums import RecommendationDecision
from app.schemas.agent_outputs import Urgency


def test_preserves_deterministic_decision(agent_seeded_engine, agent_settings):
    investigation = run_signal_investigator("C001", settings=agent_settings)
    output = run_retention_decision("C001", investigation, settings=agent_settings)
    assert output.deterministic_decision == output.agent_supported_decision
    assert output.score_consistency_valid is True


def test_c001_urgency(agent_seeded_engine, agent_settings):
    output = run_retention_decision("C001", settings=agent_settings)
    assert output.deterministic_decision == RecommendationDecision.RETAIN
    assert output.urgency in {Urgency.IMMEDIATE, Urgency.WITHIN_24_HOURS}


def test_c004_policy_warnings(agent_seeded_engine, agent_settings):
    output = run_retention_decision("C004", settings=agent_settings)
    assert output.policy_warnings


def test_c010_no_action(agent_seeded_engine, agent_settings):
    output = run_retention_decision("C010", settings=agent_settings)
    assert output.deterministic_decision == RecommendationDecision.NO_ACTION
    assert output.urgency == Urgency.NONE
