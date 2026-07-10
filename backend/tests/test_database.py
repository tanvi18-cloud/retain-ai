"""Database layer tests using temporary SQLite files."""

from datetime import date

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, select

from app.core.database import configure_engine, get_session, init_db, reset_engine
from app.models.account import Account
from app.models.alert import Alert
from app.models.audit_log import AuditLog
from app.models.bureau_trigger import BureauTrigger
from app.models.credit_profile import CreditProfile
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
from app.models.transaction_feature import TransactionFeature


@pytest.fixture
def db_engine(tmp_path) -> Engine:
    """Provide an isolated SQLite engine backed by a temporary file."""
    reset_engine()
    database_path = tmp_path / "retain_ai_test.db"
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


def _create_customer(customer_id: str = "C001") -> Customer:
    """Build a synthetic customer for tests."""
    return Customer(
        customer_id=customer_id,
        full_name="Alex Synthetic",
        segment=CustomerSegment.MASS_AFFLUENT,
        relationship_start_date=date(2020, 1, 15),
        assigned_rm_id="RM001",
        assigned_rm_name="Jordan Lee",
        assigned_rm_email="rm@example.local",
        communication_consent=True,
        preferred_channel=PreferredChannel.EMAIL,
        estimated_annual_value=12500.0,
    )


def test_init_db_creates_all_tables(db_engine: Engine) -> None:
    """init_db creates every expected application table."""
    table_names = set(SQLModel.metadata.tables.keys())

    expected_tables = {
        "customers",
        "accounts",
        "credit_profiles",
        "bureau_triggers",
        "transaction_features",
        "offers",
        "incoming_events",
        "recommendations",
        "alerts",
        "interactions",
        "audit_logs",
    }
    assert expected_tables.issubset(table_names)


def test_create_customer_and_related_records(db_session: Session) -> None:
    """Customer and related records can be persisted with foreign keys."""
    customer = _create_customer()
    db_session.add(customer)
    db_session.commit()

    account = Account(
        customer_id=customer.customer_id,
        account_type="SAVINGS",
        current_balance=15000.0,
        average_balance_90d=14200.0,
        salary_account=True,
        status="ACTIVE",
    )
    credit_profile = CreditProfile(
        customer_id=customer.customer_id,
        credit_score=720,
        max_dpd_12m=0,
        credit_utilization_pct=32.5,
        active_loans=1,
        recent_credit_inquiries=0,
        default_flag=False,
    )
    transaction_feature = TransactionFeature(
        customer_id=customer.customer_id,
        salary_received_current_month=True,
        balance_change_pct_30d=-4.2,
        monthly_inflow=8500.0,
        monthly_outflow=6200.0,
        external_transfer_amount_30d=1200.0,
        card_spend_change_pct_30d=-8.0,
        forex_spend_30d=0.0,
        competitor_transfer_detected=False,
        product_inactivity_days=3,
    )
    db_session.add(account)
    db_session.add(credit_profile)
    db_session.add(transaction_feature)
    db_session.commit()

    stored_customer = db_session.get(Customer, "C001")
    assert stored_customer is not None
    assert stored_customer.full_name == "Alex Synthetic"

    accounts = db_session.exec(select(Account).where(Account.customer_id == "C001")).all()
    assert len(accounts) == 1
    assert accounts[0].status == "ACTIVE"


def test_credit_profile_customer_id_is_unique(db_session: Session) -> None:
    """Only one credit profile may exist per customer."""
    customer = _create_customer("C002")
    db_session.add(customer)
    db_session.commit()

    first_profile = CreditProfile(
        customer_id="C002",
        credit_score=700,
        max_dpd_12m=0,
        credit_utilization_pct=25.0,
        active_loans=0,
        recent_credit_inquiries=1,
        default_flag=False,
    )
    duplicate_profile = CreditProfile(
        customer_id="C002",
        credit_score=680,
        max_dpd_12m=5,
        credit_utilization_pct=40.0,
        active_loans=1,
        recent_credit_inquiries=2,
        default_flag=False,
    )
    db_session.add(first_profile)
    db_session.commit()
    db_session.add(duplicate_profile)

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_recommendation_alert_and_interaction_flow(db_session: Session) -> None:
    """Recommendation workflow records can reference offers and events."""
    customer = _create_customer("C003")
    offer = Offer(
        offer_id="OFFER-001",
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
    )
    event = IncomingEvent(
        customer_id="C003",
        event_type="BALANCE_DROP",
        source_system="core-banking",
        payload_json={"drop_pct": 12.5},
        status=IncomingEventStatus.RECEIVED,
    )
    db_session.add(customer)
    db_session.add(offer)
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)

    recommendation = Recommendation(
        customer_id="C003",
        triggering_event_id=event.id,
        churn_score=78.0,
        value_score=65.0,
        priority_score=72.5,
        decision=RecommendationDecision.RETAIN,
        recommended_offer_id="OFFER-001",
        revenue_at_risk=4200.0,
        expected_net_benefit=1800.0,
        confidence=0.86,
        summary="High-value customer showing early churn signals.",
        evidence_json={"balance_drop_pct": 12.5},
        status=RecommendationStatus.NEW,
    )
    db_session.add(recommendation)
    db_session.commit()
    db_session.refresh(recommendation)

    alert = Alert(
        customer_id="C003",
        recommendation_id=recommendation.id,
        severity=Severity.HIGH,
        title="Retention priority customer",
        message="Review recommended offer within 24 hours.",
        assigned_rm_id="RM001",
        acknowledged=False,
    )
    interaction = Interaction(
        customer_id="C003",
        recommendation_id=recommendation.id,
        rm_id="RM001",
        action_type="OUTBOUND_CALL",
        notes="Left voicemail",
        offer_presented=False,
    )
    audit_log = AuditLog(
        entity_type="recommendation",
        entity_id=recommendation.id,
        action="CREATED",
        actor_type="system",
        details_json={"source": "scoring_pipeline"},
    )
    db_session.add(alert)
    db_session.add(interaction)
    db_session.add(audit_log)
    db_session.commit()

    stored_recommendation = db_session.exec(
        select(Recommendation).where(Recommendation.customer_id == "C003")
    ).one()
    assert stored_recommendation.status == RecommendationStatus.NEW
    assert stored_recommendation.recommended_offer_id == "OFFER-001"

    stored_alert = db_session.exec(select(Alert).where(Alert.customer_id == "C003")).one()
    assert stored_alert.acknowledged is False
    assert stored_alert.severity == Severity.HIGH


def test_get_session_dependency_uses_configured_engine(db_engine: Engine) -> None:
    """get_session yields a working session against the configured engine."""
    reset_engine()
    configure_engine(str(db_engine.url))

    session_generator = get_session()
    session = next(session_generator)

    customer = _create_customer("C004")
    session.add(customer)
    session.commit()

    assert session.get(Customer, "C004") is not None
    session_generator.close()


def test_bureau_trigger_persists(db_session: Session) -> None:
    """Bureau trigger records persist with indexed customer reference."""
    customer = _create_customer("C005")
    db_session.add(customer)
    db_session.commit()

    trigger = BureauTrigger(
        customer_id="C005",
        product_type="PERSONAL_LOAN",
        trigger_type="NEW_INQUIRY",
        institution_category="NBFC",
        amount_band="50K-100K",
        severity=Severity.MEDIUM,
        trigger_date=date(2026, 3, 1),
        source="synthetic-bureau",
        processed=False,
    )
    db_session.add(trigger)
    db_session.commit()

    stored = db_session.exec(select(BureauTrigger).where(BureauTrigger.customer_id == "C005")).one()
    assert stored.processed is False
    assert stored.severity == Severity.MEDIUM
