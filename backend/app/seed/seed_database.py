"""Synthetic seed data loader for local development and demos."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from app.core.config import BACKEND_DIR, Settings, get_settings
from app.core.database import configure_engine, get_engine, init_db, reset_engine
from app.core.exceptions import RepositoryError
from app.models.account import Account
from app.models.bureau_trigger import BureauTrigger
from app.models.credit_profile import CreditProfile
from app.models.customer import Customer
from app.models.enums import CustomerSegment, PreferredChannel, Severity
from app.models.interaction import Interaction
from app.models.offer import Offer
from app.models.transaction_feature import TransactionFeature

SEED_DIR = Path(__file__).resolve().parent
EXPECTED_CUSTOMER_IDS = tuple(f"C{index:03d}" for index in range(1, 11))
EXPECTED_OFFER_IDS = (
    "OFFER-HL-FEE",
    "OFFER-HL-RATE",
    "OFFER-CC-FEE",
    "OFFER-CC-UPGRADE",
    "OFFER-TC-UPGRADE",
    "OFFER-FD-RENEW",
    "OFFER-PRIORITY-REVIEW",
    "OFFER-REPAY-SUPPORT",
)


class SeedMetadata(BaseModel):
    """Metadata block included in each seed JSON file."""

    source_system: str
    last_updated: datetime


class CustomerSeed(BaseModel):
    """Validated customer seed record."""

    customer_id: str
    full_name: str
    segment: CustomerSegment
    relationship_start_date: date
    assigned_rm_id: str
    assigned_rm_name: str
    assigned_rm_email: str
    communication_consent: bool
    preferred_channel: PreferredChannel
    estimated_annual_value: float = Field(ge=0)


class AccountSeed(BaseModel):
    """Validated account seed record."""

    id: str
    customer_id: str
    account_type: str
    current_balance: float
    average_balance_90d: float
    salary_account: bool
    status: str
    fixed_deposit_maturity_date: date | None = None


class CreditProfileSeed(BaseModel):
    """Validated credit profile seed record."""

    id: str
    customer_id: str
    credit_score: int = Field(ge=300, le=900)
    max_dpd_12m: int = Field(ge=0)
    credit_utilization_pct: float = Field(ge=0, le=100)
    active_loans: int = Field(ge=0)
    recent_credit_inquiries: int = Field(ge=0)
    default_flag: bool
    last_updated: datetime


class BureauTriggerSeed(BaseModel):
    """Validated bureau trigger seed record."""

    id: str
    customer_id: str
    product_type: str
    trigger_type: str
    institution_category: str
    amount_band: str
    severity: Severity
    trigger_date: date
    source: str
    processed: bool


class TransactionFeatureSeed(BaseModel):
    """Validated transaction feature seed record."""

    id: str
    customer_id: str
    salary_received_current_month: bool
    balance_change_pct_30d: float
    monthly_inflow: float = Field(ge=0)
    monthly_outflow: float = Field(ge=0)
    external_transfer_amount_30d: float = Field(ge=0)
    card_spend_change_pct_30d: float
    forex_spend_30d: float = Field(ge=0)
    competitor_transfer_detected: bool
    product_inactivity_days: int = Field(ge=0)
    last_updated: datetime


class OfferSeed(BaseModel):
    """Validated offer seed record."""

    offer_id: str
    product_type: str
    offer_name: str
    description: str
    minimum_credit_score: int | None = Field(default=None, ge=300, le=900)
    maximum_dpd: int = Field(ge=0)
    minimum_customer_value: float = Field(ge=0)
    maximum_offer_cost: float = Field(ge=0)
    estimated_cost: float = Field(ge=0)
    expected_retention_uplift: float = Field(ge=0, le=1)
    active: bool
    requires_rm_approval: bool


class InteractionSeed(BaseModel):
    """Validated interaction seed record."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    recommendation_id: str | None = None
    rm_id: str
    action_type: str
    notes: str | None = None
    offer_presented: bool
    customer_response: str | None = None

    @field_validator("recommendation_id")
    @classmethod
    def recommendation_must_be_empty_in_seed(cls, value: str | None) -> str | None:
        if value is not None:
            raise ValueError("Seed interactions must not reference recommendations")
        return value


@dataclass
class SeedSummary:
    """Counts produced by a seed operation."""

    customers_inserted: int = 0
    accounts_inserted: int = 0
    credit_profiles_inserted: int = 0
    bureau_triggers_inserted: int = 0
    transaction_features_inserted: int = 0
    offers_inserted: int = 0
    interactions_inserted: int = 0
    skipped: bool = False
    messages: list[str] = field(default_factory=list)


def _load_json(filename: str) -> dict[str, Any]:
    path = SEED_DIR / filename
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_seed_payloads() -> dict[str, Any]:
    """Load and validate all seed JSON payloads."""
    core_banking = _load_json("core_banking.json")
    credit_profiles = _load_json("credit_profiles.json")
    bureau_triggers = _load_json("bureau_triggers.json")
    transaction_features = _load_json("transaction_features.json")
    offers = _load_json("offers.json")
    interactions = _load_json("interactions.json")

    customers = [CustomerSeed.model_validate(item) for item in core_banking["customers"]]
    accounts = [AccountSeed.model_validate(item) for item in core_banking["accounts"]]
    profile_items = credit_profiles["credit_profiles"]
    profiles = [CreditProfileSeed.model_validate(item) for item in profile_items]
    trigger_items = bureau_triggers["bureau_triggers"]
    triggers = [BureauTriggerSeed.model_validate(item) for item in trigger_items]
    features = [
        TransactionFeatureSeed.model_validate(item)
        for item in transaction_features["transaction_features"]
    ]
    offer_records = [OfferSeed.model_validate(item) for item in offers["offers"]]
    interaction_records = [
        InteractionSeed.model_validate(item) for item in interactions["interactions"]
    ]

    _validate_seed_consistency(
        customers=customers,
        accounts=accounts,
        profiles=profiles,
        triggers=triggers,
        features=features,
        offers=offer_records,
        interactions=interaction_records,
    )

    return {
        "metadata": {
            "core_banking": SeedMetadata.model_validate(core_banking["metadata"]),
            "credit_profiles": SeedMetadata.model_validate(credit_profiles["metadata"]),
            "bureau_triggers": SeedMetadata.model_validate(bureau_triggers["metadata"]),
            "transaction_features": SeedMetadata.model_validate(
                transaction_features["metadata"]
            ),
            "offers": SeedMetadata.model_validate(offers["metadata"]),
            "interactions": SeedMetadata.model_validate(interactions["metadata"]),
        },
        "customers": customers,
        "accounts": accounts,
        "credit_profiles": profiles,
        "bureau_triggers": triggers,
        "transaction_features": features,
        "offers": offer_records,
        "interactions": interaction_records,
    }


def _validate_seed_consistency(
    *,
    customers: list[CustomerSeed],
    accounts: list[AccountSeed],
    profiles: list[CreditProfileSeed],
    triggers: list[BureauTriggerSeed],
    features: list[TransactionFeatureSeed],
    offers: list[OfferSeed],
    interactions: list[InteractionSeed],
) -> None:
    """Validate cross-file seed constraints."""
    customer_ids = [customer.customer_id for customer in customers]
    if customer_ids != list(EXPECTED_CUSTOMER_IDS):
        raise RepositoryError(
            "Seed customers must exactly match C001 through C010",
            details={"customer_ids": customer_ids},
        )

    offer_ids = [offer.offer_id for offer in offers]
    if offer_ids != list(EXPECTED_OFFER_IDS):
        raise RepositoryError(
            "Seed offers must match the approved offer catalog",
            details={"offer_ids": offer_ids},
        )

    if len(offers) != 8:
        raise RepositoryError("Seed must contain exactly 8 approved offers")

    account_customer_ids = {account.customer_id for account in accounts}
    if not set(customer_ids).issubset(account_customer_ids):
        raise RepositoryError("Every customer must have at least one account")

    for collection_name, records in (
        ("credit_profiles", profiles),
        ("transaction_features", features),
    ):
        record_customer_ids = {record.customer_id for record in records}
        if record_customer_ids != set(customer_ids):
            raise RepositoryError(
                f"Seed {collection_name} must contain one record per customer",
                details={"customer_ids": sorted(record_customer_ids)},
            )

    trigger_customer_ids = {trigger.customer_id for trigger in triggers}
    if "C010" in trigger_customer_ids:
        raise RepositoryError("C010 must not have bureau triggers in seed data")

    c001_triggers = [trigger for trigger in triggers if trigger.customer_id == "C001"]
    if not any(
        trigger.product_type == "HOME_LOAN"
        and trigger.severity in {Severity.HIGH, Severity.CRITICAL}
        for trigger in c001_triggers
    ):
        raise RepositoryError("C001 must include a high-severity home-loan bureau trigger")

    c004_profile = next(profile for profile in profiles if profile.customer_id == "C004")
    if c004_profile.max_dpd_12m != 60:
        raise RepositoryError("C004 must have max_dpd_12m equal to 60")

    c007_feature = next(feature for feature in features if feature.customer_id == "C007")
    c007_triggers = [trigger for trigger in triggers if trigger.customer_id == "C007"]
    if c007_feature.forex_spend_30d <= 0:
        raise RepositoryError("C007 must have forex spending in seed data")
    if not any(trigger.product_type == "TRAVEL_CARD" for trigger in c007_triggers):
        raise RepositoryError("C007 must include a travel-related bureau trigger")

    c008_accounts = [account for account in accounts if account.customer_id == "C008"]
    if not any(account.fixed_deposit_maturity_date is not None for account in c008_accounts):
        raise RepositoryError("C008 must have an upcoming fixed-deposit maturity")

    for interaction in interactions:
        if interaction.customer_id not in customer_ids:
            raise RepositoryError(
                "Interaction customer references must exist in seed customers",
                details={"customer_id": interaction.customer_id},
            )


def is_seed_complete(session: Session) -> bool:
    """Return True when the full synthetic seed dataset is already present."""
    customer_count = len(session.exec(select(Customer)).all())
    offer_count = len(session.exec(select(Offer)).all())
    return customer_count == 10 and offer_count == 8


def seed_database(
    session: Session | None = None,
    *,
    engine: Engine | None = None,
    skip_if_complete: bool = True,
) -> SeedSummary:
    """Load JSON seed files and insert records in foreign-key-safe order."""
    summary = SeedSummary()
    owns_session = session is None
    active_engine = engine or get_engine()

    if session is None:
        session = Session(active_engine)

    try:
        payloads = load_seed_payloads()

        if skip_if_complete and is_seed_complete(session):
            summary.skipped = True
            summary.messages.append("Seed dataset already present; no inserts performed.")
            return summary

        for customer in payloads["customers"]:
            if session.get(Customer, customer.customer_id) is None:
                session.add(Customer(**customer.model_dump()))
                summary.customers_inserted += 1
        session.commit()

        for account in payloads["accounts"]:
            if session.get(Account, account.id) is None:
                session.add(Account(**account.model_dump()))
                summary.accounts_inserted += 1
        session.commit()

        for profile in payloads["credit_profiles"]:
            if session.get(CreditProfile, profile.id) is None:
                session.add(
                    CreditProfile(
                        **profile.model_dump(),
                    )
                )
                summary.credit_profiles_inserted += 1
        session.commit()

        for feature in payloads["transaction_features"]:
            if session.get(TransactionFeature, feature.id) is None:
                session.add(TransactionFeature(**feature.model_dump()))
                summary.transaction_features_inserted += 1
        session.commit()

        for offer in payloads["offers"]:
            if session.get(Offer, offer.offer_id) is None:
                session.add(Offer(**offer.model_dump()))
                summary.offers_inserted += 1
        session.commit()

        for trigger in payloads["bureau_triggers"]:
            if session.get(BureauTrigger, trigger.id) is None:
                session.add(BureauTrigger(**trigger.model_dump()))
                summary.bureau_triggers_inserted += 1
        session.commit()

        for interaction in payloads["interactions"]:
            if session.get(Interaction, interaction.id) is None:
                session.add(Interaction(**interaction.model_dump()))
                summary.interactions_inserted += 1
        session.commit()

        if not is_seed_complete(session):
            raise RepositoryError("Seed operation completed but dataset validation failed")

        return summary
    except ValidationError as exc:
        raise RepositoryError(
            "Seed JSON validation failed",
            details={"errors": exc.errors()},
        ) from exc
    finally:
        if owns_session:
            session.close()


def resolve_sqlite_path(database_url: str) -> Path | None:
    """Resolve a SQLite database URL to a filesystem path when applicable."""
    if not database_url.startswith("sqlite:///"):
        return None

    raw_path = database_url.removeprefix("sqlite:///")
    if raw_path == ":memory:":
        return None

    path = Path(raw_path)
    if not path.is_absolute():
        path = BACKEND_DIR / path
    return path


def reset_database(settings: Settings | None = None) -> SeedSummary:
    """Drop/recreate the database schema and reload synthetic seed data."""
    resolved_settings = settings or get_settings()
    database_path = resolve_sqlite_path(resolved_settings.database_url)

    reset_engine()
    if database_path is not None and database_path.exists():
        database_path.unlink()

    engine = configure_engine(resolved_settings.database_url)
    init_db(engine)

    with Session(engine) as session:
        return seed_database(session, engine=engine, skip_if_complete=False)


def print_seed_summary(summary: SeedSummary) -> None:
    """Print a human-readable seed summary to stdout."""
    if summary.skipped:
        print("Seed skipped: dataset already loaded.")
        return

    print("Seed completed successfully.")
    print(f"  customers inserted:           {summary.customers_inserted}")
    print(f"  accounts inserted:            {summary.accounts_inserted}")
    print(f"  credit profiles inserted:     {summary.credit_profiles_inserted}")
    print(f"  bureau triggers inserted:     {summary.bureau_triggers_inserted}")
    print(f"  transaction features inserted:{summary.transaction_features_inserted}")
    print(f"  offers inserted:              {summary.offers_inserted}")
    print(f"  interactions inserted:        {summary.interactions_inserted}")
