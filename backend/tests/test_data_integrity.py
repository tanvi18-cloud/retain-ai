"""Data integrity checks for seeded and processed RetainAI data."""

from __future__ import annotations

import json

import pytest
from sqlmodel import Session, select

from app.core.config import Settings
from app.flows.retention_flow import run_retention_flow
from app.models.alert import Alert
from app.models.analysis_execution import AnalysisExecution
from app.models.customer import Customer
from app.models.enums import AnalysisExecutionMode, EventType, IncomingEventStatus
from app.models.event import IncomingEvent
from app.models.interaction import Interaction
from app.models.offer import Offer
from app.models.recommendation import Recommendation
from app.seed.seed_database import seed_database
from app.services.analysis_execution_service import AnalysisExecutionService
from app.services.event_processor import EventProcessor


@pytest.fixture
def integrity_session(db_session: Session) -> Session:
    seed_database(db_session, skip_if_complete=False)
    return db_session


@pytest.fixture
def integrity_settings() -> Settings:
    return Settings(app_name="RetainAI", app_env="development", mock_llm_mode=True)


def _process_c001_event(session: Session, settings: Settings) -> IncomingEvent:
    event = IncomingEvent(
        customer_id="C001",
        event_type=EventType.MANUAL_REANALYSIS.value,
        source_system="CRM",
        payload_json={"reason": "integrity test"},
        status=IncomingEventStatus.RECEIVED,
        notifications_enabled=False,
    )
    session.add(event)
    session.commit()
    EventProcessor(session, settings).process_sync(event.id)
    session.commit()
    session.refresh(event)
    return event


class TestReferentialIntegrity:
    def test_no_duplicate_customer_ids(self, integrity_session: Session):
        ids = [row.customer_id for row in integrity_session.exec(select(Customer)).all()]
        assert len(ids) == len(set(ids))

    def test_no_duplicate_event_idempotency_keys(self, integrity_session: Session):
        from app.services.event_repository import EventRepository

        repo = EventRepository(integrity_session)
        key = "integrity-idem-key"
        first = repo.create_event(
            customer_id="C001",
            event_type=EventType.MANUAL_REANALYSIS.value,
            source_system="CRM",
            payload_json={"reason": "idem"},
            idempotency_key=key,
        )
        integrity_session.commit()
        duplicate_lookup = repo.get_by_idempotency_key(key)
        events = integrity_session.exec(
            select(IncomingEvent).where(IncomingEvent.idempotency_key == key)
        ).all()
        assert duplicate_lookup is not None
        assert duplicate_lookup.id == first.id
        assert len(events) == 1

    def test_no_duplicate_recommendation_for_completed_event(
        self, integrity_session: Session, integrity_settings: Settings
    ):
        event = _process_c001_event(integrity_session, integrity_settings)
        EventProcessor(integrity_session, integrity_settings).process_sync(event.id)
        integrity_session.commit()
        recs = integrity_session.exec(
            select(Recommendation).where(Recommendation.triggering_event_id == event.id)
        ).all()
        assert len(recs) == 1

    def test_no_duplicate_final_alert_for_event(
        self, integrity_session: Session, integrity_settings: Settings
    ):
        event = _process_c001_event(integrity_session, integrity_settings)
        EventProcessor(integrity_session, integrity_settings).process_sync(event.id)
        integrity_session.commit()
        alerts = integrity_session.exec(select(Alert).where(Alert.event_id == event.id)).all()
        agent_alerts = [
            alert for alert in alerts if alert.alert_type.value == "AGENT_RECOMMENDATION"
        ]
        assert len(agent_alerts) <= 1

    def test_recommendation_offer_ids_exist(
        self, integrity_session: Session, integrity_settings: Settings
    ):
        _process_c001_event(integrity_session, integrity_settings)
        for rec in integrity_session.exec(select(Recommendation)).all():
            if rec.recommended_offer_id:
                assert integrity_session.get(Offer, rec.recommended_offer_id) is not None
            if rec.alternate_offer_id:
                assert integrity_session.get(Offer, rec.alternate_offer_id) is not None

    def test_selected_offers_are_active(
        self, integrity_session: Session, integrity_settings: Settings
    ):
        _process_c001_event(integrity_session, integrity_settings)
        for rec in integrity_session.exec(select(Recommendation)).all():
            if rec.recommended_offer_id:
                offer = integrity_session.get(Offer, rec.recommended_offer_id)
                assert offer is not None
                assert offer.active is True

    def test_recommendation_customer_ids_exist(self, integrity_session: Session):
        for rec in integrity_session.exec(select(Recommendation)).all():
            assert integrity_session.get(Customer, rec.customer_id) is not None

    def test_event_customer_ids_exist(
        self, integrity_session: Session, integrity_settings: Settings
    ):
        event = _process_c001_event(integrity_session, integrity_settings)
        assert integrity_session.get(Customer, event.customer_id) is not None

    def test_interaction_recommendation_ids_exist(self, integrity_session: Session):
        for interaction in integrity_session.exec(select(Interaction)).all():
            if interaction.recommendation_id:
                assert (
                    integrity_session.get(Recommendation, interaction.recommendation_id) is not None
                )

    def test_analysis_executions_reference_valid_customers(
        self, integrity_session: Session, integrity_settings: Settings
    ):
        _process_c001_event(integrity_session, integrity_settings)
        for execution in integrity_session.exec(select(AnalysisExecution)).all():
            assert integrity_session.get(Customer, execution.customer_id) is not None


class TestValueRanges:
    def test_non_negative_monetary_values(
        self, integrity_session: Session, integrity_settings: Settings
    ):
        _process_c001_event(integrity_session, integrity_settings)
        for rec in integrity_session.exec(select(Recommendation)).all():
            assert rec.revenue_at_risk >= 0
            assert rec.expected_net_benefit >= 0

    def test_scores_in_range(self, integrity_session: Session, integrity_settings: Settings):
        _process_c001_event(integrity_session, integrity_settings)
        for rec in integrity_session.exec(select(Recommendation)).all():
            assert 0 <= rec.churn_score <= 100
            assert 0 <= rec.value_score <= 100
            assert 0 <= rec.priority_score <= 100
            assert 0 <= rec.confidence <= 1

    def test_json_fields_serializable(
        self, integrity_session: Session, integrity_settings: Settings
    ):
        _process_c001_event(integrity_session, integrity_settings)
        for rec in integrity_session.exec(select(Recommendation)).all():
            json.dumps(rec.evidence_json)
            json.dumps(rec.rm_brief_json)
            json.dumps(rec.policy_warnings_json)
            json.dumps(rec.validation_warnings_json)

    def test_source_timestamps_are_valid(self, integrity_session: Session):
        for customer in integrity_session.exec(select(Customer)).all():
            assert customer.created_at is not None
            assert customer.updated_at is not None


class TestPostFlowIntegrity:
    def test_integrity_after_multi_customer_flows(
        self, integrity_session: Session, integrity_settings: Settings
    ):
        for customer_id in ("C001", "C004", "C008", "C010"):
            execution = AnalysisExecutionService(integrity_session).create_execution(
                customer_id=customer_id,
                mode=AnalysisExecutionMode.AGENTIC,
            )
            integrity_session.commit()
            run_retention_flow(
                integrity_session,
                execution_id=execution.id,
                customer_id=customer_id,
                settings=integrity_settings,
                notifications_enabled=False,
            )
            integrity_session.commit()

        customer_ids = [row.customer_id for row in integrity_session.exec(select(Customer)).all()]
        assert len(customer_ids) == len(set(customer_ids))
