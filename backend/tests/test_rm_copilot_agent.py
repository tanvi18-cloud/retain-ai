"""Tests for RM Copilot agent."""

from app.agents.offer_strategy_agent import run_offer_strategy
from app.agents.retention_decision_agent import run_retention_decision
from app.agents.rm_copilot_agent import run_rm_copilot
from app.agents.signal_investigator import run_signal_investigator


def test_actionable_talking_points(agent_seeded_engine, agent_settings):
    output = run_rm_copilot("C001", settings=agent_settings)
    assert len(output.talking_points) >= 2
    assert output.recommended_action


def test_prohibited_claims_included(agent_seeded_engine, agent_settings):
    output = run_rm_copilot("C001", settings=agent_settings)
    assert output.prohibited_claims


def test_evidence_references(agent_seeded_engine, agent_settings):
    investigation = run_signal_investigator("C001", settings=agent_settings)
    decision = run_retention_decision("C001", investigation, settings=agent_settings)
    offer = run_offer_strategy("C001", investigation, decision, settings=agent_settings)
    output = run_rm_copilot("C001", investigation, decision, offer, settings=agent_settings)
    assert output.evidence_references


def test_no_approval_promises(agent_seeded_engine, agent_settings):
    output = run_rm_copilot("C001", settings=agent_settings)
    combined = " ".join([output.executive_summary, *output.talking_points]).lower()
    assert "guaranteed approval" not in combined
    assert "pre-approved" not in combined


def test_c010_no_action_brief(agent_seeded_engine, agent_settings):
    output = run_rm_copilot("C010", settings=agent_settings)
    assert "no action" in output.headline.lower() or "stable" in output.headline.lower()
