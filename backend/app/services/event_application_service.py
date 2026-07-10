"""Apply inbound events to synthetic source-system records."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from sqlmodel import Session, select

from app.models.account import Account
from app.models.bureau_trigger import BureauTrigger
from app.models.credit_profile import CreditProfile
from app.models.customer import Customer
from app.models.enums import EventType, Severity
from app.models.event import IncomingEvent
from app.models.transaction_feature import TransactionFeature
from app.services.audit_log_service import write_audit_log

COMPETITOR_DESTINATIONS = frozenset(
    {"OTHER_BANK", "COMPETITOR", "EXTERNAL_BANK", "PRIVATE_BANK", "NBFC"}
)


def _utc_now() -> datetime:
    return datetime.now(UTC)


class EventApplicationService:
    """Mutate synthetic Customer 360 source records from validated events."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def apply_event(
        self, event: IncomingEvent, validated_payload: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Apply event mutations and return audit change records."""
        event_type = EventType(event.event_type)
        if event_type == EventType.MANUAL_REANALYSIS:
            return []

        handler = {
            EventType.EXTERNAL_HOME_LOAN_INQUIRY: self._apply_home_loan_inquiry,
            EventType.EXTERNAL_CARD_INQUIRY: self._apply_card_inquiry,
            EventType.SALARY_CREDIT_STOPPED: self._apply_salary_stopped,
            EventType.SALARY_CREDIT_RESUMED: self._apply_salary_resumed,
            EventType.LARGE_EXTERNAL_TRANSFER: self._apply_large_transfer,
            EventType.FIXED_DEPOSIT_MATURITY: self._apply_fd_maturity,
            EventType.FOREX_SPEND_INCREASE: self._apply_forex_increase,
            EventType.DPD_CHANGED: self._apply_dpd_changed,
            EventType.PRODUCT_USAGE_DECLINE: self._apply_product_decline,
            EventType.BALANCE_DECLINE: self._apply_balance_decline,
            EventType.INVESTMENT_TRANSFER_INCREASE: self._apply_investment_transfer,
        }[event_type]

        return handler(event, validated_payload)

    def _apply_home_loan_inquiry(
        self,
        event: IncomingEvent,
        payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return self._create_bureau_trigger(
            event,
            payload,
            product_type="HOME_LOAN",
        )

    def _apply_card_inquiry(
        self,
        event: IncomingEvent,
        payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return self._create_bureau_trigger(
            event,
            payload,
            product_type="CREDIT_CARD",
        )

    def _create_bureau_trigger(
        self,
        event: IncomingEvent,
        payload: dict[str, Any],
        *,
        product_type: str,
    ) -> list[dict[str, Any]]:
        trigger = BureauTrigger(
            customer_id=event.customer_id,
            product_type=product_type,
            trigger_type="EXTERNAL_INQUIRY",
            institution_category=payload.get("institution_category") or "EXTERNAL",
            amount_band=payload.get("amount_band") or "UNKNOWN",
            severity=Severity(payload["severity"]),
            trigger_date=payload.get("trigger_date") or date.today(),
            source=event.source_system,
            processed=False,
        )
        self.session.add(trigger)
        self.session.flush()
        change = {
            "entity": "bureau_triggers",
            "entity_id": trigger.id,
            "before": None,
            "after": {
                "product_type": product_type,
                "severity": payload["severity"],
                "source": event.source_system,
            },
        }
        write_audit_log(
            self.session,
            entity_type="bureau_triggers",
            entity_id=trigger.id,
            action="EVENT_APPLIED",
            actor_type="EVENT_PROCESSOR",
            actor_id=event.id,
            details={"event_id": event.id, "change": change},
        )
        return [change]

    def _get_or_create_features(self, customer_id: str) -> TransactionFeature:
        feature = self.session.exec(
            select(TransactionFeature).where(TransactionFeature.customer_id == customer_id)
        ).first()
        if feature is not None:
            return feature
        feature = TransactionFeature(
            customer_id=customer_id,
            salary_received_current_month=True,
            balance_change_pct_30d=0.0,
            monthly_inflow=0.0,
            monthly_outflow=0.0,
            external_transfer_amount_30d=0.0,
            card_spend_change_pct_30d=0.0,
            forex_spend_30d=0.0,
            competitor_transfer_detected=False,
            product_inactivity_days=0,
            last_updated=_utc_now(),
        )
        self.session.add(feature)
        self.session.flush()
        return feature

    def _update_features(
        self,
        event: IncomingEvent,
        *,
        before: dict[str, Any],
        after: dict[str, Any],
    ) -> list[dict[str, Any]]:
        change = {
            "entity": "transaction_features",
            "entity_id": event.customer_id,
            "before": before,
            "after": after,
        }
        write_audit_log(
            self.session,
            entity_type="transaction_features",
            entity_id=event.customer_id,
            action="EVENT_APPLIED",
            actor_type="EVENT_PROCESSOR",
            actor_id=event.id,
            details={"event_id": event.id, "change": change},
        )
        return [change]

    def _apply_salary_stopped(
        self,
        event: IncomingEvent,
        payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        feature = self._get_or_create_features(event.customer_id)
        before = {"salary_received_current_month": feature.salary_received_current_month}
        feature.salary_received_current_month = False
        feature.last_updated = _utc_now()
        return self._update_features(
            event, before=before, after={"salary_received_current_month": False}
        )

    def _apply_salary_resumed(
        self,
        event: IncomingEvent,
        payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        feature = self._get_or_create_features(event.customer_id)
        before = {"salary_received_current_month": feature.salary_received_current_month}
        feature.salary_received_current_month = True
        feature.last_updated = _utc_now()
        return self._update_features(
            event, before=before, after={"salary_received_current_month": True}
        )

    def _apply_large_transfer(
        self,
        event: IncomingEvent,
        payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        feature = self._get_or_create_features(event.customer_id)
        destination = (payload.get("destination_category") or "").upper()
        competitor = destination in COMPETITOR_DESTINATIONS
        before = {
            "external_transfer_amount_30d": feature.external_transfer_amount_30d,
            "competitor_transfer_detected": feature.competitor_transfer_detected,
        }
        feature.external_transfer_amount_30d = float(payload["amount"])
        if competitor:
            feature.competitor_transfer_detected = True
        feature.last_updated = _utc_now()
        after = {
            "external_transfer_amount_30d": feature.external_transfer_amount_30d,
            "competitor_transfer_detected": feature.competitor_transfer_detected,
        }
        return self._update_features(event, before=before, after=after)

    def _apply_fd_maturity(
        self,
        event: IncomingEvent,
        payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        changes: list[dict[str, Any]] = []
        maturity_date = date.fromisoformat(str(payload["maturity_date"]))
        account_id = payload.get("account_id")
        statement = select(Account).where(
            Account.customer_id == event.customer_id,
            Account.account_type == "FIXED_DEPOSIT",
        )
        if account_id:
            statement = statement.where(Account.id == account_id)
        account = self.session.exec(statement).first()
        if account is not None:
            before = {"fixed_deposit_maturity_date": str(account.fixed_deposit_maturity_date)}
            account.fixed_deposit_maturity_date = maturity_date
            account.updated_at = _utc_now()
            after = {"fixed_deposit_maturity_date": str(maturity_date)}
            change = {
                "entity": "accounts",
                "entity_id": account.id,
                "before": before,
                "after": after,
            }
            changes.append(change)
            write_audit_log(
                self.session,
                entity_type="accounts",
                entity_id=account.id,
                action="EVENT_APPLIED",
                actor_type="EVENT_PROCESSOR",
                actor_id=event.id,
                details={"event_id": event.id, "change": change},
            )

        if payload.get("external_outflow_detected"):
            feature = self._get_or_create_features(event.customer_id)
            before = {"external_transfer_amount_30d": feature.external_transfer_amount_30d}
            amount = float(payload.get("maturity_amount") or 100_000.0)
            feature.external_transfer_amount_30d = max(feature.external_transfer_amount_30d, amount)
            feature.last_updated = _utc_now()
            changes.extend(
                self._update_features(
                    event,
                    before=before,
                    after={"external_transfer_amount_30d": feature.external_transfer_amount_30d},
                )
            )
        return changes

    def _apply_forex_increase(
        self,
        event: IncomingEvent,
        payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        feature = self._get_or_create_features(event.customer_id)
        before = {"forex_spend_30d": feature.forex_spend_30d}
        feature.forex_spend_30d = float(payload["forex_spend_30d"])
        feature.last_updated = _utc_now()
        return self._update_features(
            event,
            before=before,
            after={"forex_spend_30d": feature.forex_spend_30d},
        )

    def _apply_dpd_changed(
        self,
        event: IncomingEvent,
        payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        profile = self.session.exec(
            select(CreditProfile).where(CreditProfile.customer_id == event.customer_id)
        ).first()
        if profile is None:
            profile = CreditProfile(
                customer_id=event.customer_id,
                credit_score=650,
                max_dpd_12m=0,
                credit_utilization_pct=0.0,
                active_loans=0,
                recent_credit_inquiries=0,
                default_flag=False,
                last_updated=_utc_now(),
            )
            self.session.add(profile)
            self.session.flush()
        before = {"max_dpd_12m": profile.max_dpd_12m}
        profile.max_dpd_12m = int(payload["new_dpd"])
        profile.last_updated = _utc_now()
        change = {
            "entity": "credit_profiles",
            "entity_id": profile.id,
            "before": before,
            "after": {"max_dpd_12m": profile.max_dpd_12m},
        }
        write_audit_log(
            self.session,
            entity_type="credit_profiles",
            entity_id=profile.id,
            action="EVENT_APPLIED",
            actor_type="EVENT_PROCESSOR",
            actor_id=event.id,
            details={"event_id": event.id, "change": change},
        )
        return [change]

    def _apply_product_decline(
        self,
        event: IncomingEvent,
        payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        feature = self._get_or_create_features(event.customer_id)
        before = {
            "product_inactivity_days": feature.product_inactivity_days,
            "card_spend_change_pct_30d": feature.card_spend_change_pct_30d,
        }
        feature.product_inactivity_days = int(payload["product_inactivity_days"])
        if payload.get("card_spend_change_pct_30d") is not None:
            feature.card_spend_change_pct_30d = float(payload["card_spend_change_pct_30d"])
        feature.last_updated = _utc_now()
        after = {
            "product_inactivity_days": feature.product_inactivity_days,
            "card_spend_change_pct_30d": feature.card_spend_change_pct_30d,
        }
        return self._update_features(event, before=before, after=after)

    def _apply_balance_decline(
        self,
        event: IncomingEvent,
        payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        feature = self._get_or_create_features(event.customer_id)
        before = {"balance_change_pct_30d": feature.balance_change_pct_30d}
        feature.balance_change_pct_30d = float(payload["balance_change_pct_30d"])
        feature.last_updated = _utc_now()
        return self._update_features(
            event,
            before=before,
            after={"balance_change_pct_30d": feature.balance_change_pct_30d},
        )

    def _apply_investment_transfer(
        self,
        event: IncomingEvent,
        payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        feature = self._get_or_create_features(event.customer_id)
        before = {"external_transfer_amount_30d": feature.external_transfer_amount_30d}
        feature.external_transfer_amount_30d = float(payload["external_transfer_amount_30d"])
        feature.last_updated = _utc_now()
        changes = self._update_features(
            event,
            before=before,
            after={"external_transfer_amount_30d": feature.external_transfer_amount_30d},
        )
        write_audit_log(
            self.session,
            entity_type="incoming_events",
            entity_id=event.id,
            action="INVESTMENT_PATTERN_RECORDED",
            actor_type="EVENT_PROCESSOR",
            actor_id=event.id,
            details={
                "destination_category": payload["destination_category"],
                "external_transfer_amount_30d": payload["external_transfer_amount_30d"],
            },
        )
        return changes

    def get_customer(self, customer_id: str) -> Customer | None:
        """Load customer for notification routing."""
        return self.session.get(Customer, customer_id)
