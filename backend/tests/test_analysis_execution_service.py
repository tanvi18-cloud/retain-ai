"""Analysis execution service tests."""

import pytest

from app.core.exceptions import AnalysisExecutionNotFoundError, ResourceNotFoundError
from app.models.enums import AnalysisExecutionMode, AnalysisExecutionStatus
from app.services.analysis_execution_service import AnalysisExecutionService


def test_create_execution(agent_seeded_session):
    service = AnalysisExecutionService(agent_seeded_session)
    execution = service.create_execution(
        customer_id="C001",
        mode=AnalysisExecutionMode.AGENTIC,
    )
    assert execution.status == AnalysisExecutionStatus.QUEUED
    assert execution.customer_id == "C001"


def test_missing_customer(agent_seeded_session):
    service = AnalysisExecutionService(agent_seeded_session)
    with pytest.raises(ResourceNotFoundError):
        service.create_execution(customer_id="C999", mode=AnalysisExecutionMode.AGENTIC)


def test_mark_running_and_completed(agent_seeded_session):
    service = AnalysisExecutionService(agent_seeded_session)
    execution = service.create_execution(
        customer_id="C001",
        mode=AnalysisExecutionMode.AGENTIC,
    )
    service.mark_running(execution, current_step="LOAD")
    service.update_step(execution, "CREW")
    service.mark_completed(
        execution,
        recommendation_id=None,
        priority_score=84,
        validation_warnings=["test warning"],
    )
    detail = service.get_detail(execution.id)
    assert detail.status == AnalysisExecutionStatus.COMPLETED
    assert detail.priority_score == 84
    assert detail.validation_warnings == ["test warning"]


def test_mark_failed(agent_seeded_session):
    service = AnalysisExecutionService(agent_seeded_session)
    execution = service.create_execution(
        customer_id="C001",
        mode=AnalysisExecutionMode.AGENTIC,
    )
    service.mark_failed(
        execution,
        error_code="TEST_ERROR",
        safe_error_message="Safe message only",
    )
    detail = service.get_detail(execution.id)
    assert detail.status == AnalysisExecutionStatus.FAILED
    assert detail.safe_error_message == "Safe message only"


def test_idempotency_key(agent_seeded_session):
    service = AnalysisExecutionService(agent_seeded_session)
    first = service.create_execution(
        customer_id="C001",
        mode=AnalysisExecutionMode.AGENTIC,
        idempotency_key="idem-1",
    )
    second = service.create_execution(
        customer_id="C001",
        mode=AnalysisExecutionMode.AGENTIC,
        idempotency_key="idem-1",
    )
    assert first.id == second.id


def test_list_by_customer(agent_seeded_session):
    service = AnalysisExecutionService(agent_seeded_session)
    service.create_execution(customer_id="C001", mode=AnalysisExecutionMode.AGENTIC)
    service.create_execution(customer_id="C002", mode=AnalysisExecutionMode.AGENTIC)
    page = service.list_by_customer("C001")
    assert page.total >= 1
    assert all(item.customer_id == "C001" for item in page.items)


def test_get_missing_execution(agent_seeded_session):
    service = AnalysisExecutionService(agent_seeded_session)
    with pytest.raises(AnalysisExecutionNotFoundError):
        service.get_by_id("missing-id")
