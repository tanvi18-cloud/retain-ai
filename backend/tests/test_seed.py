"""Synthetic seed data tests."""

from datetime import date

import pytest
from pydantic import ValidationError
from sqlmodel import Session, select

from app.core.config import Settings
from app.core.database import configure_engine, get_engine, init_db, reset_engine
from app.models.account import Account
from app.models.bureau_trigger import BureauTrigger
from app.models.credit_profile import CreditProfile
from app.models.customer import Customer
from app.models.enums import Severity
from app.models.interaction import Interaction
from app.models.offer import Offer
from app.models.transaction_feature import TransactionFeature
from app.seed.seed_database import (
    EXPECTED_CUSTOMER_IDS,
    EXPECTED_OFFER_IDS,
    InteractionSeed,
    is_seed_complete,
    load_seed_payloads,
    reset_database,
    seed_database,
)


@pytest.fixture
def seed_settings(tmp_path) -> Settings:
    """Settings pointing at a temporary SQLite database."""
    database_path = tmp_path / "seed_test.db"
    return Settings(database_url=f"sqlite:///{database_path.as_posix()}")


@pytest.fixture
def seeded_db(seed_settings: Settings):
    """Provide a session with a freshly seeded temporary database."""
    reset_engine()
    configure_engine(seed_settings.database_url)
    init_db()
    with Session(get_engine()) as session:
        seed_database(session, skip_if_complete=False)
        yield session
    reset_engine()


def test_load_seed_payloads_validates_expected_catalog() -> None:
    """Seed JSON validates to exactly 10 customers and 8 offers."""
    payloads = load_seed_payloads()

    assert len(payloads["customers"]) == 10
    assert len(payloads["offers"]) == 8
    assert [customer.customer_id for customer in payloads["customers"]] == list(
        EXPECTED_CUSTOMER_IDS
    )
    assert [offer.offer_id for offer in payloads["offers"]] == list(EXPECTED_OFFER_IDS)


def test_seed_creates_expected_dataset(seeded_db: Session) -> None:
    """Seed inserts the full synthetic dataset."""
    assert len(seeded_db.exec(select(Customer)).all()) == 10
    assert len(seeded_db.exec(select(Offer)).all()) == 8
    assert len(seeded_db.exec(select(CreditProfile)).all()) == 10
    assert len(seeded_db.exec(select(TransactionFeature)).all()) == 10
    assert len(seeded_db.exec(select(Account)).all()) >= 10
    assert is_seed_complete(seeded_db)


def test_customer_ids_c001_through_c010_exist(seeded_db: Session) -> None:
    """All required customer IDs exist after seeding."""
    for customer_id in EXPECTED_CUSTOMER_IDS:
        assert seeded_db.get(Customer, customer_id) is not None


def test_c001_has_high_severity_home_loan_trigger(seeded_db: Session) -> None:
    """C001 includes a high-severity home-loan bureau trigger."""
    triggers = seeded_db.exec(
        select(BureauTrigger).where(BureauTrigger.customer_id == "C001")
    ).all()

    assert any(
        trigger.product_type == "HOME_LOAN"
        and trigger.severity in {Severity.HIGH, Severity.CRITICAL}
        for trigger in triggers
    )


def test_c004_has_max_dpd_60(seeded_db: Session) -> None:
    """C004 credit profile reflects 60 days past due."""
    profile = seeded_db.exec(select(CreditProfile).where(CreditProfile.customer_id == "C004")).one()

    assert profile.max_dpd_12m == 60


def test_c007_has_forex_and_travel_trigger(seeded_db: Session) -> None:
    """C007 reflects forex spending and a travel-card bureau trigger."""
    feature = seeded_db.exec(
        select(TransactionFeature).where(TransactionFeature.customer_id == "C007")
    ).one()
    triggers = seeded_db.exec(
        select(BureauTrigger).where(BureauTrigger.customer_id == "C007")
    ).all()

    assert feature.forex_spend_30d > 0
    assert any(trigger.product_type == "TRAVEL_CARD" for trigger in triggers)


def test_c008_has_upcoming_fixed_deposit_maturity(seeded_db: Session) -> None:
    """C008 includes a fixed-deposit account with a maturity date."""
    accounts = seeded_db.exec(select(Account).where(Account.customer_id == "C008")).all()

    maturity_dates = [
        account.fixed_deposit_maturity_date
        for account in accounts
        if account.fixed_deposit_maturity_date is not None
    ]
    assert maturity_dates
    assert maturity_dates[0] >= date(2026, 1, 1)


def test_c010_has_no_bureau_triggers(seeded_db: Session) -> None:
    """C010 has no material bureau triggers in the seed dataset."""
    triggers = seeded_db.exec(
        select(BureauTrigger).where(BureauTrigger.customer_id == "C010")
    ).all()

    assert triggers == []


def test_seed_is_idempotent(seeded_db: Session) -> None:
    """Running seed twice does not create duplicate records."""
    first_customer_count = len(seeded_db.exec(select(Customer)).all())
    first_offer_count = len(seeded_db.exec(select(Offer)).all())

    summary = seed_database(seeded_db, skip_if_complete=True)

    assert summary.skipped is True
    assert len(seeded_db.exec(select(Customer)).all()) == first_customer_count == 10
    assert len(seeded_db.exec(select(Offer)).all()) == first_offer_count == 8


def test_reset_mode_recreates_expected_dataset(seed_settings: Settings) -> None:
    """Reset mode rebuilds the database and reloads all seed records."""
    reset_engine()
    summary = reset_database(seed_settings)

    configure_engine(seed_settings.database_url)
    with Session(get_engine()) as session:
        assert summary.customers_inserted == 10
        assert summary.offers_inserted == 8
        assert len(session.exec(select(Customer)).all()) == 10
        assert len(session.exec(select(Interaction)).all()) == 6
        assert is_seed_complete(session)

    reset_engine()


def test_interaction_seed_rejects_recommendation_reference() -> None:
    """Seed interactions must not reference recommendations."""
    with pytest.raises(ValidationError):
        InteractionSeed.model_validate(
            {
                "id": "INT-BAD",
                "customer_id": "C001",
                "recommendation_id": "REC-001",
                "rm_id": "RM001",
                "action_type": "EMAIL",
                "notes": "Invalid seed record",
                "offer_presented": False,
                "customer_response": None,
            }
        )
