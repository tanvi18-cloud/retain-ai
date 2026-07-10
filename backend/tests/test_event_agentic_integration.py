"""Event processor agentic integration tests."""

import pytest
from sqlmodel import Session, select

from app.core.config import Settings
from app.models.alert import Alert
from app.models.enums import AlertType, EventType, IncomingEventStatus
from app.models.event import IncomingEvent
from app.models.recommendation import Recommendation
from app.seed.seed_database import seed_database
from app.services.event_application_service import EventApplicationService
from app.services.event_processor import EventProcessor


@pytest.fixture
def integration_settings() -> Settings:
    return Settings(
        app_name="RetainAI",
        app_env="development",
        mock_llm_mode=True,
        run_full_crew_min_priority=50,
        create_alert_min_priority=50,
    )


@pytest.fixture
def integration_session(db_session: Session) -> Session:
    seed_database(db_session, skip_if_complete=False)
    return db_session


def _create_event(session: Session, customer_id: str, event_type: EventType) -> IncomingEvent:
    event = IncomingEvent(
        customer_id=customer_id,
        event_type=event_type.value,
        source_system="CRM",
        payload_json={"reason": "integration test"},
        status=IncomingEventStatus.RECEIVED,
        notifications_enabled=False,
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


def test_event_invokes_flow(integration_session: Session, integration_settings: Settings):
    event = _create_event(integration_session, "C001", EventType.MANUAL_REANALYSIS)
    processor = EventProcessor(integration_session, integration_settings)
    processor.process_sync(event.id)
    refreshed = integration_session.get(IncomingEvent, event.id)
    assert refreshed is not None
    assert refreshed.status == IncomingEventStatus.COMPLETED
    assert refreshed.execution_id is not None
    assert refreshed.analysis_result_json is not None


def test_event_links_recommendation(integration_session: Session, integration_settings: Settings):
    event = _create_event(integration_session, "C001", EventType.MANUAL_REANALYSIS)
    EventProcessor(integration_session, integration_settings).process_sync(event.id)
    refreshed = integration_session.get(IncomingEvent, event.id)
    recs = integration_session.exec(
        select(Recommendation).where(Recommendation.triggering_event_id == event.id)
    ).all()
    assert recs
    assert refreshed.analysis_result_json.get("recommendation_id") == recs[0].id


def test_retry_does_not_duplicate_recommendation(
    integration_session: Session, integration_settings: Settings
):
    event = _create_event(integration_session, "C001", EventType.MANUAL_REANALYSIS)
    processor = EventProcessor(integration_session, integration_settings)
    processor.process_sync(event.id)
    processor.process_sync(event.id)
    recs = integration_session.exec(
        select(Recommendation).where(Recommendation.triggering_event_id == event.id)
    ).all()
    assert len(recs) == 1


def test_retry_does_not_duplicate_alert(
    integration_session: Session, integration_settings: Settings
):
    event = _create_event(integration_session, "C001", EventType.MANUAL_REANALYSIS)
    processor = EventProcessor(integration_session, integration_settings)
    processor.process_sync(event.id)
    processor.process_sync(event.id)
    alerts = integration_session.exec(
        select(Alert).where(
            Alert.event_id == event.id,
            Alert.alert_type == AlertType.AGENT_RECOMMENDATION,
        )
    ).all()
    assert len(alerts) <= 1


def test_manual_reanalysis_does_not_mutate(integration_session: Session):
    from app.models.transaction_feature import TransactionFeature

    before = integration_session.exec(
        select(TransactionFeature).where(TransactionFeature.customer_id == "C001")
    ).one()
    event = _create_event(integration_session, "C001", EventType.MANUAL_REANALYSIS)
    changes = EventApplicationService(integration_session).apply_event(event, event.payload_json)
    after = integration_session.exec(
        select(TransactionFeature).where(TransactionFeature.customer_id == "C001")
    ).one()
    assert changes == []
    assert before.model_dump() == after.model_dump()


def test_c010_no_alert(integration_session: Session, integration_settings: Settings):
    event = _create_event(integration_session, "C010", EventType.MANUAL_REANALYSIS)
    EventProcessor(integration_session, integration_settings).process_sync(event.id)
    alerts = integration_session.exec(
        select(Alert).where(Alert.customer_id == "C010")
    ).all()
    agent_alerts = [a for a in alerts if a.alert_type == AlertType.AGENT_RECOMMENDATION]
    assert agent_alerts == []
