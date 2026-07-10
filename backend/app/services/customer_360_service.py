"""Customer 360 aggregation service."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import ResourceNotFoundError
from app.models.enums import FreshnessStatus
from app.schemas.customer_360 import (
    Customer360DataFreshness,
    Customer360Response,
    DataFreshnessSource,
)
from app.services.account_repository import AccountRepository
from app.services.bureau_trigger_repository import BureauTriggerRepository
from app.services.credit_profile_repository import CreditProfileRepository
from app.services.customer_repository import CustomerRepository
from app.services.interaction_repository import InteractionRepository
from app.services.recommendation_repository import RecommendationRepository
from app.services.transaction_feature_repository import TransactionFeatureRepository


def _ensure_utc(value: datetime) -> datetime:
    """Normalize a datetime to UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _freshness_status(
    last_updated: datetime | None,
    *,
    threshold_hours: int,
    now: datetime,
) -> FreshnessStatus:
    """Calculate freshness status for a source timestamp."""
    if last_updated is None:
        return FreshnessStatus.MISSING

    age_hours = (_ensure_utc(now) - _ensure_utc(last_updated)).total_seconds() / 3600
    if age_hours > threshold_hours:
        return FreshnessStatus.STALE
    return FreshnessStatus.FRESH


class Customer360Service:
    """Assemble the Customer 360 view from repository-backed sources."""

    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.customers = CustomerRepository(session)
        self.accounts = AccountRepository(session)
        self.credit_profiles = CreditProfileRepository(session)
        self.transaction_features = TransactionFeatureRepository(session)
        self.bureau_triggers = BureauTriggerRepository(session)
        self.recommendations = RecommendationRepository(session)
        self.interactions = InteractionRepository(session)

    def get_customer_360(self, customer_id: str) -> Customer360Response:
        """Build the Customer 360 response for a customer."""
        try:
            customer = self.customers.get_by_id(customer_id)
        except ResourceNotFoundError as exc:
            raise ResourceNotFoundError(
                code="CUSTOMER_NOT_FOUND",
                message=f"Customer {customer_id} was not found",
            ) from exc

        accounts = self.accounts.list_by_customer(customer_id)
        credit_profile = self.credit_profiles.get_by_customer(customer_id)
        transaction_features = self.transaction_features.get_by_customer(customer_id)
        bureau_triggers = self.bureau_triggers.list_by_customer(customer_id)
        recommendations = self.recommendations.list_all_by_customer(customer_id)
        interactions = self.interactions.list_recent_by_customer(customer_id, limit=10)

        now = datetime.now(UTC)
        core_banking_updated = customer.updated_at
        if accounts:
            account_updates = [account.updated_at for account in accounts]
            core_banking_updated = max(customer.updated_at, *account_updates)

        core_banking_status = _freshness_status(
            core_banking_updated,
            threshold_hours=self.settings.core_banking_stale_hours,
            now=now,
        )
        credit_history_status = _freshness_status(
            credit_profile.last_updated if credit_profile else None,
            threshold_hours=self.settings.credit_profile_stale_hours,
            now=now,
        )
        bureau_trigger_updated = (
            max((trigger.created_at for trigger in bureau_triggers), default=None)
            if bureau_triggers
            else None
        )
        bureau_trigger_status = _freshness_status(
            bureau_trigger_updated,
            threshold_hours=self.settings.bureau_trigger_stale_hours,
            now=now,
        )
        transaction_history_status = _freshness_status(
            transaction_features.last_updated if transaction_features else None,
            threshold_hours=self.settings.transaction_feature_stale_hours,
            now=now,
        )

        data_freshness = Customer360DataFreshness(
            core_banking=DataFreshnessSource(
                last_updated=core_banking_updated,
                status=core_banking_status,
            ),
            credit_history=DataFreshnessSource(
                last_updated=credit_profile.last_updated if credit_profile else None,
                status=credit_history_status,
            ),
            bureau_triggers=DataFreshnessSource(
                last_updated=bureau_trigger_updated,
                status=bureau_trigger_status,
            ),
            transaction_history=DataFreshnessSource(
                last_updated=transaction_features.last_updated if transaction_features else None,
                status=transaction_history_status,
            ),
        )

        warnings = self._build_warnings(
            customer_consent=customer.communication_consent,
            credit_profile_present=credit_profile is not None,
            transaction_features_present=transaction_features is not None,
            bureau_triggers_present=bool(bureau_triggers),
            data_freshness=data_freshness,
        )

        return Customer360Response(
            customer=customer,
            accounts=accounts,
            credit_profile=credit_profile,
            bureau_triggers=bureau_triggers,
            transaction_features=transaction_features,
            recommendations=recommendations,
            interactions=interactions,
            data_freshness=data_freshness,
            data_warnings=warnings,
        )

    @staticmethod
    def _build_warnings(
        *,
        customer_consent: bool,
        credit_profile_present: bool,
        transaction_features_present: bool,
        bureau_triggers_present: bool,
        data_freshness: Customer360DataFreshness,
    ) -> list[str]:
        """Build non-fatal Customer 360 data quality warnings."""
        warnings: list[str] = []

        if not credit_profile_present:
            warnings.append("missing credit profile")
        if not transaction_features_present:
            warnings.append("missing transaction features")
        if not bureau_triggers_present:
            warnings.append("no recent bureau trigger")
        if not customer_consent:
            warnings.append("communication consent disabled")

        stale_sources = [
            name
            for name, source in (
                ("core banking", data_freshness.core_banking),
                ("credit history", data_freshness.credit_history),
                ("bureau triggers", data_freshness.bureau_triggers),
                ("transaction history", data_freshness.transaction_history),
            )
            if source.status == FreshnessStatus.STALE
        ]
        if stale_sources:
            warnings.append(f"stale source data: {', '.join(stale_sources)}")

        return warnings
