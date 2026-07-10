"""Alert service tests."""

import pytest
from sqlmodel import Session, select

from app.core.config import Settings
from app.models.alert import Alert
from app.models.customer import Customer
from app.models.enums import AlertType, EventType, RecommendationDecision, Severity
from app.models.event import IncomingEvent
from app.seed.seed_database import seed_database
from app.services.alert_service import AlertService
from app.services.analysis_service import AnalysisService


@pytest.fixture
def seeded_alert_session(db_session: Session) -> Session:
    seed_database(db_session, skip_if_complete=False)
    return db_session


@pytest.fixture
def alert_settings() -> Settings:
    return Settings(app_name="RetainAI", app_env="development")


def test_high_priority_creates_alert(seeded_alert_session: Session, alert_settings: Settings):
    analysis = AnalysisService(seeded_alert_session).analyze_customer_rules_only("C001")
    customer = seeded_alert_session.get(Customer, "C001")
    event = IncomingEvent(
        customer_id="C001",
        event_type=EventType.EXTERNAL_HOME_LOAN_INQUIRY.value,
        source_system="CREDIT_BUREAU",
        payload_json={"severity": "HIGH"},
    )
    seeded_alert_session.add(event)
    seeded_alert_session.commit()
    service = AlertService(seeded_alert_session, alert_settings)
    alert = service.create_preview_alert_if_needed(
        event=event,
        analysis=analysis,
        customer=customer,
    )
    assert alert is not None
    assert alert.severity in {Severity.HIGH, Severity.CRITICAL}


def test_no_action_does_not_create_alert(seeded_alert_session: Session, alert_settings: Settings):
    analysis = AnalysisService(seeded_alert_session).analyze_customer_rules_only("C010")
    customer = seeded_alert_session.get(Customer, "C010")
    event = IncomingEvent(
        customer_id="C010",
        event_type=EventType.MANUAL_REANALYSIS.value,
        source_system="CRM",
        payload_json={},
    )
    seeded_alert_session.add(event)
    seeded_alert_session.commit()
    service = AlertService(seeded_alert_session, alert_settings)
    alert = service.create_preview_alert_if_needed(
        event=event,
        analysis=analysis,
        customer=customer,
    )
    assert alert is None
    assert analysis.priority_result.decision == RecommendationDecision.NO_ACTION


def test_duplicate_event_does_not_create_duplicate_alert(
    seeded_alert_session: Session,
    alert_settings: Settings,
):
    analysis = AnalysisService(seeded_alert_session).analyze_customer_rules_only("C001")
    customer = seeded_alert_session.get(Customer, "C001")
    event = IncomingEvent(
        customer_id="C001",
        event_type=EventType.MANUAL_REANALYSIS.value,
        source_system="CRM",
        payload_json={},
    )
    seeded_alert_session.add(event)
    seeded_alert_session.commit()
    service = AlertService(seeded_alert_session, alert_settings)
    first = service.create_preview_alert_if_needed(
        event=event, analysis=analysis, customer=customer
    )
    second = service.create_preview_alert_if_needed(
        event=event, analysis=analysis, customer=customer
    )
    seeded_alert_session.commit()
    assert first is not None
    assert second is not None
    assert first.id == second.id
    alerts = seeded_alert_session.exec(
        select(Alert).where(Alert.event_id == event.id, Alert.alert_type == AlertType.RULES_PREVIEW)
    ).all()
    assert len(alerts) == 1


def test_acknowledge_is_idempotent(seeded_alert_session: Session, alert_settings: Settings):
    analysis = AnalysisService(seeded_alert_session).analyze_customer_rules_only("C001")
    customer = seeded_alert_session.get(Customer, "C001")
    event = IncomingEvent(
        customer_id="C001",
        event_type=EventType.MANUAL_REANALYSIS.value,
        source_system="CRM",
        payload_json={},
    )
    seeded_alert_session.add(event)
    seeded_alert_session.commit()
    service = AlertService(seeded_alert_session, alert_settings)
    alert = service.create_preview_alert_if_needed(
        event=event, analysis=analysis, customer=customer
    )
    seeded_alert_session.commit()
    first = service.acknowledge_alert(alert.id, rm_id="RM001")
    second = service.acknowledge_alert(alert.id, rm_id="RM001")
    assert first.acknowledged is True
    assert second.acknowledged is True
