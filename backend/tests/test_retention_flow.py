"""Retention flow routing and orchestration tests."""

import pytest
from sqlmodel import select

from app.core.config import Settings
from app.flows.retention_flow import RetentionFlowRunner, run_retention_flow
from app.models.enums import (
    AnalysisExecutionMode,
    AnalysisExecutionStatus,
)
from app.models.recommendation import Recommendation
from app.schemas.flow_state import RetentionFlowState
from app.services.analysis_execution_service import AnalysisExecutionService


@pytest.fixture
def flow_settings() -> Settings:
    return Settings(
        app_name="RetainAI",
        app_env="development",
        mock_llm_mode=True,
        persist_no_action_recommendations=True,
        run_full_crew_min_priority=50,
        create_alert_min_priority=50,
        send_email_min_priority=70,
    )


def _create_execution(session, customer_id: str) -> str:
    execution = AnalysisExecutionService(session).create_execution(
        customer_id=customer_id,
        mode=AnalysisExecutionMode.AGENTIC,
    )
    session.commit()
    return execution.id


def test_c001_runs_full_crew(flow_settings: Settings, agent_seeded_session):
    execution_id = _create_execution(agent_seeded_session, "C001")
    result = run_retention_flow(
        agent_seeded_session,
        execution_id=execution_id,
        customer_id="C001",
        settings=flow_settings,
    )
    assert result.agentic_analysis_ran is True
    assert result.recommendation_id is not None
    assert result.status == "COMPLETED"


def test_c010_skips_crew(flow_settings: Settings, agent_seeded_session):
    execution_id = _create_execution(agent_seeded_session, "C010")
    result = run_retention_flow(
        agent_seeded_session,
        execution_id=execution_id,
        customer_id="C010",
        settings=flow_settings,
    )
    assert result.agentic_analysis_ran is False
    assert result.alert_id is None


def test_c008_runs_full_crew(flow_settings: Settings, agent_seeded_session):
    execution_id = _create_execution(agent_seeded_session, "C008")
    result = run_retention_flow(
        agent_seeded_session,
        execution_id=execution_id,
        customer_id="C008",
        settings=flow_settings,
    )
    assert result.agentic_analysis_ran is True
    assert result.recommendation_id is not None


def test_priority_50_creates_alert(flow_settings: Settings, agent_seeded_session):
    execution_id = _create_execution(agent_seeded_session, "C001")
    result = run_retention_flow(
        agent_seeded_session,
        execution_id=execution_id,
        customer_id="C001",
        settings=flow_settings,
    )
    assert result.priority_score >= 50
    assert result.alert_id is not None


def test_execution_marked_completed(flow_settings: Settings, agent_seeded_session):
    execution_id = _create_execution(agent_seeded_session, "C001")
    run_retention_flow(
        agent_seeded_session,
        execution_id=execution_id,
        customer_id="C001",
        settings=flow_settings,
    )
    execution = AnalysisExecutionService(agent_seeded_session).get_by_id(execution_id)
    assert execution.status == AnalysisExecutionStatus.COMPLETED


def test_critical_validation_prevents_persistence(flow_settings: Settings, agent_seeded_session):
    execution_id = _create_execution(agent_seeded_session, "C001")
    runner = RetentionFlowRunner(agent_seeded_session, flow_settings)

    def _bad_validate(**_kwargs):
        from datetime import UTC, datetime

        from app.schemas.crew_result import FinalPolicyValidationResult

        return FinalPolicyValidationResult(
            valid=False,
            corrected=False,
            errors=["forced failure"],
            warnings=[],
            rejected_fields=[],
            corrected_fields=[],
            validated_at=datetime.now(UTC),
            policy_version="test",
        )

    runner.policy_validator.validate_crew_result = _bad_validate  # type: ignore[method-assign]
    state = RetentionFlowState(execution_id=execution_id, customer_id="C001")
    result = runner.execute(state)
    assert result.status == "FAILED"
    recs = agent_seeded_session.exec(
        select(Recommendation).where(Recommendation.analysis_execution_id == execution_id)
    ).all()
    assert recs == []


def test_notifications_disabled_still_persists(flow_settings: Settings, agent_seeded_session):
    execution_id = _create_execution(agent_seeded_session, "C001")
    result = run_retention_flow(
        agent_seeded_session,
        execution_id=execution_id,
        customer_id="C001",
        notifications_enabled=False,
        settings=flow_settings,
    )
    assert result.recommendation_id is not None
    assert result.status == "COMPLETED"


def test_c004_runs_crew_when_priority_met(flow_settings: Settings, agent_seeded_session):
    execution_id = _create_execution(agent_seeded_session, "C004")
    result = run_retention_flow(
        agent_seeded_session,
        execution_id=execution_id,
        customer_id="C004",
        settings=flow_settings,
    )
    if result.priority_score >= flow_settings.run_full_crew_min_priority:
        assert result.agentic_analysis_ran is True
