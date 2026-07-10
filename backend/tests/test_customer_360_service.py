"""Customer 360 service tests."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlmodel import Session, select

from app.core.config import Settings
from app.core.database import configure_engine, get_engine, init_db, reset_engine
from app.models.credit_profile import CreditProfile
from app.models.customer import Customer
from app.models.enums import FreshnessStatus, Severity
from app.seed.seed_database import seed_database
from app.services.customer_360_service import Customer360Service


@pytest.fixture
def seeded_session(tmp_path):
    """Provide a session containing the full synthetic seed dataset."""
    reset_engine()
    database_path = tmp_path / "customer_360_test.db"
    settings = Settings(database_url=f"sqlite:///{database_path.as_posix()}")
    configure_engine(settings.database_url)
    init_db()
    with Session(get_engine()) as session:
        seed_database(session, skip_if_complete=False)
        yield session, settings
    reset_engine()


def test_c001_customer_360_contains_expected_sections(seeded_session) -> None:
    """C001 Customer 360 includes core profile and related records."""
    session, settings = seeded_session
    service = Customer360Service(session, settings=settings)

    response = service.get_customer_360("C001")

    assert response.customer.customer_id == "C001"
    assert response.customer.full_name == "Ananya Deshmukh"
    assert len(response.accounts) >= 1
    assert response.credit_profile is not None
    assert response.transaction_features is not None


def test_c001_contains_home_loan_bureau_trigger(seeded_session) -> None:
    """C001 includes a home-loan bureau trigger."""
    session, settings = seeded_session
    service = Customer360Service(session, settings=settings)

    response = service.get_customer_360("C001")

    assert any(
        trigger.product_type == "HOME_LOAN"
        and trigger.severity in {Severity.HIGH, Severity.CRITICAL}
        for trigger in response.bureau_triggers
    )


def test_c004_contains_60_dpd(seeded_session) -> None:
    """C004 credit profile reflects 60 DPD."""
    session, settings = seeded_session
    service = Customer360Service(session, settings=settings)

    response = service.get_customer_360("C004")

    assert response.credit_profile is not None
    assert response.credit_profile.max_dpd_12m == 60


def test_c008_contains_fixed_deposit_maturity(seeded_session) -> None:
    """C008 includes an account with a fixed-deposit maturity date."""
    session, settings = seeded_session
    service = Customer360Service(session, settings=settings)

    response = service.get_customer_360("C008")

    assert any(account.fixed_deposit_maturity_date is not None for account in response.accounts)


def test_c010_has_no_material_bureau_trigger(seeded_session) -> None:
    """C010 has no bureau triggers and emits a warning."""
    session, settings = seeded_session
    service = Customer360Service(session, settings=settings)

    response = service.get_customer_360("C010")

    assert response.bureau_triggers == []
    assert "no recent bureau trigger" in response.data_warnings
    assert response.data_freshness.bureau_triggers.status == FreshnessStatus.MISSING


def test_missing_optional_source_produces_warning(seeded_session) -> None:
    """Missing credit profile returns warnings instead of failing."""
    session, settings = seeded_session
    profile = session.exec(select(CreditProfile).where(CreditProfile.customer_id == "C002")).one()
    session.delete(profile)
    session.commit()

    service = Customer360Service(session, settings=settings)
    response = service.get_customer_360("C002")

    assert response.credit_profile is None
    assert "missing credit profile" in response.data_warnings
    assert response.data_freshness.credit_history.status == FreshnessStatus.MISSING


def test_stale_source_detection(seeded_session) -> None:
    """Stale timestamps produce STALE freshness and warnings."""
    session, settings = seeded_session
    stale_settings = settings.model_copy(update={"credit_profile_stale_hours": 1})
    profile = session.exec(select(CreditProfile).where(CreditProfile.customer_id == "C001")).one()
    profile.last_updated = datetime.now(UTC) - timedelta(hours=48)
    session.add(profile)
    session.commit()

    service = Customer360Service(session, settings=stale_settings)
    response = service.get_customer_360("C001")

    assert response.data_freshness.credit_history.status == FreshnessStatus.STALE
    assert any("credit history" in warning for warning in response.data_warnings)
    assert any("stale source data" in warning for warning in response.data_warnings)


def test_communication_consent_warning(seeded_session) -> None:
    """Disabled communication consent produces a warning."""
    session, settings = seeded_session
    customer = session.get(Customer, "C001")
    assert customer is not None
    customer.communication_consent = False
    session.add(customer)
    session.commit()

    service = Customer360Service(session, settings=settings)
    response = service.get_customer_360("C001")

    assert "communication consent disabled" in response.data_warnings


def test_recommendations_default_to_empty_list(seeded_session) -> None:
    """Customers without recommendations return an empty list."""
    session, settings = seeded_session
    service = Customer360Service(session, settings=settings)

    response = service.get_customer_360("C010")

    assert response.recommendations == []
