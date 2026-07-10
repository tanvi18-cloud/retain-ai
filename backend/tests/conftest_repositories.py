"""Repository and schema test fixtures."""

from datetime import UTC, date, datetime

import pytest
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel

from app.core.database import configure_engine, init_db, reset_engine
from app.models.alert import Alert
from app.models.customer import Customer
from app.models.enums import (
    CustomerSegment,
    IncomingEventStatus,
    PreferredChannel,
    RecommendationDecision,
    RecommendationStatus,
    Severity,
)
from app.models.event import IncomingEvent
from app.models.interaction import Interaction
from app.models.offer import Offer
from app.models.recommendation import Recommendation


@pytest.fixture
def db_engine(tmp_path):
    """Provide an isolated SQLite engine backed by a temporary file."""
    reset_engine()
    database_path = tmp_path / "repository_test.db"
    engine = configure_engine(f"sqlite:///{database_path.as_posix()}")
    init_db(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)
    reset_engine()


@pytest.fixture
def db_session(db_engine: Engine) -> Session:
    """Provide a database session bound to the temporary test engine."""
    with Session(db_engine) as session:
        yield session


@pytest.fixture
def seeded_session(db_session: Session) -> Session:
    """Seed representative synthetic records for repository tests."""
    customers = [
        Customer(
            customer_id="C001",
            full_name="Alex Synthetic",
            segment=CustomerSegment.MASS_AFFLUENT,
            relationship_start_date=date(2020, 1, 15),
            assigned_rm_id="RM001",
            assigned_rm_name="Jordan Lee",
            assigned_rm_email="rm@example.local",
            communication_consent=True,
            preferred_channel=PreferredChannel.EMAIL,
            estimated_annual_value=12500.0,
        ),
        Customer(
            customer_id="C002",
            full_name="Blake Standard",
            segment=CustomerSegment.STANDARD,
            relationship_start_date=date(2019, 6, 1),
            assigned_rm_id="RM001",
            assigned_rm_name="Jordan Lee",
            assigned_rm_email="rm@example.local",
            communication_consent=True,
            preferred_channel=PreferredChannel.PHONE,
            estimated_annual_value=4200.0,
        ),
        Customer(
            customer_id="C003",
            full_name="Casey Priority",
            segment=CustomerSegment.PRIORITY,
            relationship_start_date=date(2018, 3, 10),
            assigned_rm_id="RM002",
            assigned_rm_name="Taylor Kim",
            assigned_rm_email="taylor@example.local",
            communication_consent=True,
            preferred_channel=PreferredChannel.SMS,
            estimated_annual_value=28000.0,
        ),
    ]
    offers = [
        Offer(
            offer_id="OFFER-ACTIVE",
            product_type="CREDIT_CARD",
            offer_name="Fee Waiver",
            description="Waive annual fee for 12 months",
            maximum_dpd=30,
            minimum_customer_value=5000.0,
            maximum_offer_cost=250.0,
            estimated_cost=150.0,
            expected_retention_uplift=0.18,
            active=True,
            requires_rm_approval=False,
        ),
        Offer(
            offer_id="OFFER-INACTIVE",
            product_type="LOAN",
            offer_name="Rate Discount",
            description="Reduce loan rate by 50 bps",
            maximum_dpd=15,
            minimum_customer_value=10000.0,
            maximum_offer_cost=500.0,
            estimated_cost=300.0,
            expected_retention_uplift=0.12,
            active=False,
            requires_rm_approval=True,
        ),
    ]
    db_session.add_all(customers)
    db_session.add_all(offers)
    db_session.commit()

    event = IncomingEvent(
        customer_id="C001",
        event_type="BALANCE_DROP",
        source_system="core-banking",
        payload_json={"drop_pct": 12.5},
        status=IncomingEventStatus.RECEIVED,
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)

    older_recommendation = Recommendation(
        customer_id="C001",
        triggering_event_id=event.id,
        churn_score=65.0,
        value_score=55.0,
        priority_score=60.0,
        decision=RecommendationDecision.MONITOR,
        recommended_offer_id="OFFER-ACTIVE",
        revenue_at_risk=2500.0,
        expected_net_benefit=900.0,
        confidence=0.72,
        summary="Earlier monitoring recommendation",
        evidence_json={"signal": "balance_drop"},
        status=RecommendationStatus.REVIEWED,
        created_at=datetime(2026, 1, 10, tzinfo=UTC),
        updated_at=datetime(2026, 1, 10, tzinfo=UTC),
    )
    latest_recommendation = Recommendation(
        customer_id="C001",
        triggering_event_id=event.id,
        churn_score=82.0,
        value_score=70.0,
        priority_score=78.0,
        decision=RecommendationDecision.RETAIN,
        recommended_offer_id="OFFER-ACTIVE",
        revenue_at_risk=4200.0,
        expected_net_benefit=1800.0,
        confidence=0.91,
        summary="Latest retention recommendation",
        evidence_json={"signal": "competitor_transfer"},
        status=RecommendationStatus.NEW,
        created_at=datetime(2026, 2, 10, tzinfo=UTC),
        updated_at=datetime(2026, 2, 10, tzinfo=UTC),
    )
    db_session.add(older_recommendation)
    db_session.add(latest_recommendation)
    db_session.commit()
    db_session.refresh(latest_recommendation)

    alerts = [
        Alert(
            customer_id="C001",
            recommendation_id=latest_recommendation.id,
            severity=Severity.HIGH,
            title="Retention priority",
            message="Contact customer within 24 hours",
            assigned_rm_id="RM001",
            acknowledged=False,
        ),
        Alert(
            customer_id="C002",
            recommendation_id=latest_recommendation.id,
            severity=Severity.LOW,
            title="Acknowledged alert",
            message="Already reviewed",
            assigned_rm_id="RM001",
            acknowledged=True,
        ),
    ]
    interactions = [
        Interaction(
            customer_id="C001",
            recommendation_id=latest_recommendation.id,
            rm_id="RM001",
            action_type="OUTBOUND_CALL",
            notes="Left voicemail",
            offer_presented=False,
        ),
        Interaction(
            customer_id="C001",
            rm_id="RM001",
            action_type="EMAIL",
            notes="Sent follow-up email",
            offer_presented=True,
            customer_response="Requested callback",
        ),
    ]
    extra_event = IncomingEvent(
        customer_id="C001",
        event_type="CARD_SPEND_DROP",
        source_system="cards",
        payload_json={"drop_pct": 8.0},
        status=IncomingEventStatus.COMPLETED,
    )
    db_session.add_all(alerts)
    db_session.add_all(interactions)
    db_session.add(extra_event)
    db_session.commit()
    return db_session
