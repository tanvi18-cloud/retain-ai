"""Recommendation persistence service tests."""

import pytest

from app.core.config import Settings
from app.crews.retention_crew import RetentionCrew
from app.models.enums import AnalysisExecutionMode, CreatedByMode, RecommendationStatus
from app.services.analysis_execution_service import AnalysisExecutionService
from app.services.analysis_service import AnalysisService
from app.services.recommendation_service import RecommendationService


@pytest.fixture
def rec_settings() -> Settings:
    return Settings(app_name="RetainAI", app_env="development", mock_llm_mode=True)


def test_recommendation_persisted(rec_settings: Settings, agent_seeded_session):
    analysis = AnalysisService(agent_seeded_session).analyze_customer_rules_only("C001")
    execution = AnalysisExecutionService(agent_seeded_session).create_execution(
        customer_id="C001",
        mode=AnalysisExecutionMode.AGENTIC,
    )
    service = RecommendationService(agent_seeded_session, rec_settings)
    rec = service.create_from_rules_analysis(
        analysis=analysis,
        execution_id=execution.id,
    )
    assert rec.id
    assert rec.status == RecommendationStatus.NEW


def test_previous_recommendation_preserved(rec_settings: Settings, agent_seeded_session):
    analysis = AnalysisService(agent_seeded_session).analyze_customer_rules_only("C001")
    execution1 = AnalysisExecutionService(agent_seeded_session).create_execution(
        customer_id="C001",
        mode=AnalysisExecutionMode.AGENTIC,
    )
    execution2 = AnalysisExecutionService(agent_seeded_session).create_execution(
        customer_id="C001",
        mode=AnalysisExecutionMode.AGENTIC,
    )
    service = RecommendationService(agent_seeded_session, rec_settings)
    first = service.create_from_rules_analysis(analysis=analysis, execution_id=execution1.id)
    second = service.create_from_rules_analysis(analysis=analysis, execution_id=execution2.id)
    assert first.id != second.id


def test_execution_linked(rec_settings: Settings, agent_seeded_session):
    analysis = AnalysisService(agent_seeded_session).analyze_customer_rules_only("C008")
    execution = AnalysisExecutionService(agent_seeded_session).create_execution(
        customer_id="C008",
        mode=AnalysisExecutionMode.AGENTIC,
    )
    rec = RecommendationService(agent_seeded_session, rec_settings).create_from_rules_analysis(
        analysis=analysis,
        execution_id=execution.id,
    )
    assert rec.analysis_execution_id == execution.id


def test_duplicate_event_does_not_duplicate(rec_settings: Settings, agent_seeded_session):
    from app.models.enums import IncomingEventStatus
    from app.models.event import IncomingEvent

    event = IncomingEvent(
        customer_id="C001",
        event_type="MANUAL_REANALYSIS",
        source_system="CRM",
        payload_json={},
        status=IncomingEventStatus.RECEIVED,
    )
    agent_seeded_session.add(event)
    agent_seeded_session.commit()
    agent_seeded_session.refresh(event)

    analysis = AnalysisService(agent_seeded_session).analyze_customer_rules_only("C001")
    execution = AnalysisExecutionService(agent_seeded_session).create_execution(
        customer_id="C001",
        mode=AnalysisExecutionMode.AGENTIC,
        event_id=event.id,
    )
    service = RecommendationService(agent_seeded_session, rec_settings)
    first = service.create_from_rules_analysis(
        analysis=analysis,
        execution_id=execution.id,
        event_id=event.id,
    )
    second = service.create_from_rules_analysis(
        analysis=analysis,
        execution_id=execution.id,
        event_id=event.id,
    )
    assert first.id == second.id


def test_no_chain_of_thought_fields_stored(rec_settings: Settings, agent_seeded_session):
    analysis = AnalysisService(agent_seeded_session).analyze_customer_rules_only("C001")
    crew_result = RetentionCrew(rec_settings).kickoff(execution_id="exec-cot", customer_id="C001")
    execution = AnalysisExecutionService(agent_seeded_session).create_execution(
        customer_id="C001",
        mode=AnalysisExecutionMode.AGENTIC,
    )
    rec = RecommendationService(agent_seeded_session, rec_settings).create_from_crew_result(
        analysis=analysis,
        crew_result=crew_result,
        execution_id=execution.id,
    )
    serialized = rec.model_dump()
    assert "chain_of_thought" not in serialized
    assert "raw_prompt" not in serialized


def test_crew_recommendation_created_by_mode(rec_settings: Settings, agent_seeded_session):
    analysis = AnalysisService(agent_seeded_session).analyze_customer_rules_only("C001")
    crew_result = RetentionCrew(rec_settings).kickoff(execution_id="exec-mode", customer_id="C001")
    execution = AnalysisExecutionService(agent_seeded_session).create_execution(
        customer_id="C001",
        mode=AnalysisExecutionMode.AGENTIC,
    )
    rec = RecommendationService(agent_seeded_session, rec_settings).create_from_crew_result(
        analysis=analysis,
        crew_result=crew_result,
        execution_id=execution.id,
    )
    assert rec.created_by_mode == CreatedByMode.MOCK
