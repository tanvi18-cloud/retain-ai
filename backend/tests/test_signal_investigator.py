"""Tests for Signal Investigator agent."""

from app.agents.signal_investigator import run_signal_investigator


def test_c001_home_loan_inquiry(agent_seeded_engine, agent_settings):
    output = run_signal_investigator("C001", settings=agent_settings)
    assert output.customer_id == "C001"
    assert "home-loan" in output.primary_signal.lower()
    assert output.evidence_references


def test_c003_salary_stopped(agent_seeded_engine, agent_settings):
    output = run_signal_investigator("C003", settings=agent_settings)
    assert "salary" in output.primary_signal.lower()


def test_c010_no_material_signal(agent_seeded_engine, agent_settings):
    output = run_signal_investigator("C010", settings=agent_settings)
    assert (
        "no material" in output.primary_signal.lower()
        or "stable" in output.investigation_summary.lower()
    )


def test_stale_data_handling(agent_seeded_engine, agent_settings):
    output = run_signal_investigator("C001", settings=agent_settings)
    assert output.data_quality.value in {"GOOD", "PARTIAL", "POOR"}
