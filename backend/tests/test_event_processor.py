"""Event processor tests."""

import pytest
from sqlmodel import Session, select

from app.core.config import Settings
from app.models.bureau_trigger import BureauTrigger
from app.models.credit_profile import CreditProfile
from app.models.enums import EventType, IncomingEventStatus
from app.models.event import IncomingEvent
from app.models.transaction_feature import TransactionFeature
from app.seed.seed_database import seed_database
from app.services.analysis_service import AnalysisService
from app.services.event_application_service import EventApplicationService
from app.services.event_processor import EventProcessor, analysis_snapshot


@pytest.fixture
def seeded_processor_session(db_session: Session) -> Session:
    seed_database(db_session, skip_if_complete=False)
    return db_session


@pytest.fixture
def processor_settings() -> Settings:
    return Settings(app_name="RetainAI", app_env="development")


def _create_event(
    session: Session,
    *,
    customer_id: str,
    event_type: EventType,
    payload: dict,
) -> IncomingEvent:
    event = IncomingEvent(
        customer_id=customer_id,
        event_type=event_type.value,
        source_system="CREDIT_BUREAU",
        payload_json=payload,
        status=IncomingEventStatus.RECEIVED,
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


def test_home_loan_inquiry_creates_bureau_trigger(
    seeded_processor_session: Session,
    processor_settings: Settings,
):
    event = _create_event(
        seeded_processor_session,
        customer_id="C001",
        event_type=EventType.EXTERNAL_HOME_LOAN_INQUIRY,
        payload={"severity": "HIGH", "institution_category": "PRIVATE_BANK"},
    )
    service = EventApplicationService(seeded_processor_session)
    changes = service.apply_event(event, event.payload_json)
    seeded_processor_session.commit()
    assert changes
    triggers = seeded_processor_session.exec(
        select(BureauTrigger).where(BureauTrigger.customer_id == "C001")
    ).all()
    assert any(t.product_type == "HOME_LOAN" for t in triggers)


def test_salary_stopped_updates_transaction_feature(
    seeded_processor_session: Session,
):
    event = _create_event(
        seeded_processor_session,
        customer_id="C001",
        event_type=EventType.SALARY_CREDIT_STOPPED,
        payload={},
    )
    EventApplicationService(seeded_processor_session).apply_event(event, event.payload_json)
    seeded_processor_session.commit()
    feature = seeded_processor_session.exec(
        select(TransactionFeature).where(TransactionFeature.customer_id == "C001")
    ).one()
    assert feature.salary_received_current_month is False


def test_dpd_changed_updates_credit_profile(seeded_processor_session: Session):
    event = _create_event(
        seeded_processor_session,
        customer_id="C004",
        event_type=EventType.DPD_CHANGED,
        payload={"new_dpd": 75},
    )
    EventApplicationService(seeded_processor_session).apply_event(event, event.payload_json)
    seeded_processor_session.commit()
    profile = seeded_processor_session.exec(
        select(CreditProfile).where(CreditProfile.customer_id == "C004")
    ).one()
    assert profile.max_dpd_12m == 75


def test_manual_reanalysis_does_not_mutate(seeded_processor_session: Session):
    before = seeded_processor_session.exec(
        select(TransactionFeature).where(TransactionFeature.customer_id == "C001")
    ).one()
    event = _create_event(
        seeded_processor_session,
        customer_id="C001",
        event_type=EventType.MANUAL_REANALYSIS,
        payload={"reason": "test"},
    )
    changes = EventApplicationService(seeded_processor_session).apply_event(
        event, event.payload_json
    )
    after = seeded_processor_session.exec(
        select(TransactionFeature).where(TransactionFeature.customer_id == "C001")
    ).one()
    assert changes == []
    assert before.model_dump() == after.model_dump()


def test_processing_marks_completed(
    seeded_processor_session: Session,
    processor_settings: Settings,
):
    event = _create_event(
        seeded_processor_session,
        customer_id="C001",
        event_type=EventType.MANUAL_REANALYSIS,
        payload={"reason": "review"},
    )
    processor = EventProcessor(seeded_processor_session, processor_settings)
    processor.process_sync(event.id)
    refreshed = seeded_processor_session.get(IncomingEvent, event.id)
    assert refreshed is not None
    assert refreshed.status == IncomingEventStatus.COMPLETED
    assert refreshed.processed_at is not None
    assert refreshed.analysis_result_json is not None


def test_analysis_snapshot_structure(seeded_processor_session: Session):
    analysis = AnalysisService(seeded_processor_session).analyze_customer_rules_only("C001")
    snapshot = analysis_snapshot(analysis)
    assert snapshot["customer_id"] == "C001"
    assert "priority_score" in snapshot
