"""Incoming event API schemas and payload validation."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import Field, field_validator

from app.models.enums import EventType, IncomingEventStatus, Severity
from app.schemas.common import APIModel, validate_non_negative_amount, validate_score


class IncomingEventCreate(APIModel):
    """Payload for ingesting an inbound event."""

    customer_id: str = Field(min_length=1, max_length=32)
    event_type: EventType
    source_system: str = Field(min_length=1, max_length=128)
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = Field(default=None, max_length=128)
    notifications_enabled: bool = True


class IncomingEventResponse(APIModel):
    """Async event ingestion response."""

    event_id: str
    customer_id: str
    event_type: EventType
    source_system: str
    status: IncomingEventStatus
    execution_id: str | None = None
    created_at: datetime
    queued_at: datetime | None = None
    processing_started_at: datetime | None = None
    processed_at: datetime | None = None
    error_message: str | None = None
    duplicate: bool = False
    analysis_summary: dict[str, Any] | None = None


class IncomingEventSummary(APIModel):
    """Compact incoming event representation."""

    event_id: str
    customer_id: str
    event_type: str
    source_system: str
    status: IncomingEventStatus
    created_at: datetime


class IncomingEventDetail(APIModel):
    """Full incoming event representation."""

    event_id: str
    customer_id: str
    event_type: str
    source_system: str
    payload_json: dict[str, Any]
    idempotency_key: str | None
    execution_id: str | None
    analysis_result_json: dict[str, Any] | None
    status: IncomingEventStatus
    error_message: str | None
    retry_count: int
    notifications_enabled: bool
    created_at: datetime
    queued_at: datetime | None
    processing_started_at: datetime | None
    processed_at: datetime | None


class EventPayloadBase(APIModel):
    """Base class for validated event payloads."""


class ExternalHomeLoanInquiryPayload(EventPayloadBase):
    severity: Severity
    amount_band: str | None = None
    institution_category: str | None = None
    trigger_date: date | None = None


class ExternalCardInquiryPayload(EventPayloadBase):
    severity: Severity
    card_type: str | None = None
    trigger_date: date | None = None


class SalaryCreditStoppedPayload(EventPayloadBase):
    effective_month: str | None = None
    previous_monthly_salary: float | None = None

    @field_validator("previous_monthly_salary")
    @classmethod
    def validate_salary(cls, value: float | None) -> float | None:
        if value is None:
            return None
        return validate_non_negative_amount(value)


class SalaryCreditResumedPayload(EventPayloadBase):
    effective_month: str | None = None


class LargeExternalTransferPayload(EventPayloadBase):
    amount: float
    destination_category: str | None = None
    transaction_date: date | None = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: float) -> float:
        return validate_non_negative_amount(value)


class FixedDepositMaturityPayload(EventPayloadBase):
    account_id: str | None = None
    maturity_date: date
    maturity_amount: float | None = None
    external_outflow_detected: bool | None = None

    @field_validator("maturity_amount")
    @classmethod
    def validate_amount(cls, value: float | None) -> float | None:
        if value is None:
            return None
        return validate_non_negative_amount(value)


class ForexSpendIncreasePayload(EventPayloadBase):
    forex_spend_30d: float
    percentage_increase: float | None = None
    travel_trigger_detected: bool | None = None

    @field_validator("forex_spend_30d")
    @classmethod
    def validate_forex(cls, value: float) -> float:
        return validate_non_negative_amount(value)

    @field_validator("percentage_increase")
    @classmethod
    def validate_pct(cls, value: float | None) -> float | None:
        if value is None:
            return None
        validate_score(value)
        return value


class DpdChangedPayload(EventPayloadBase):
    previous_dpd: int | None = Field(default=None, ge=0)
    new_dpd: int = Field(ge=0)


class ProductUsageDeclinePayload(EventPayloadBase):
    product_inactivity_days: int = Field(ge=0)
    card_spend_change_pct_30d: float | None = None


class BalanceDeclinePayload(EventPayloadBase):
    balance_change_pct_30d: float


class InvestmentTransferIncreasePayload(EventPayloadBase):
    external_transfer_amount_30d: float
    destination_category: str
    percentage_increase: float | None = None

    @field_validator("external_transfer_amount_30d")
    @classmethod
    def validate_transfer(cls, value: float) -> float:
        return validate_non_negative_amount(value)

    @field_validator("percentage_increase")
    @classmethod
    def validate_pct(cls, value: float | None) -> float | None:
        if value is None:
            return None
        validate_score(value)
        return value


class ManualReanalysisPayload(EventPayloadBase):
    reason: str | None = None


EVENT_PAYLOAD_MODELS: dict[EventType, type[EventPayloadBase]] = {
    EventType.EXTERNAL_HOME_LOAN_INQUIRY: ExternalHomeLoanInquiryPayload,
    EventType.EXTERNAL_CARD_INQUIRY: ExternalCardInquiryPayload,
    EventType.SALARY_CREDIT_STOPPED: SalaryCreditStoppedPayload,
    EventType.SALARY_CREDIT_RESUMED: SalaryCreditResumedPayload,
    EventType.LARGE_EXTERNAL_TRANSFER: LargeExternalTransferPayload,
    EventType.FIXED_DEPOSIT_MATURITY: FixedDepositMaturityPayload,
    EventType.FOREX_SPEND_INCREASE: ForexSpendIncreasePayload,
    EventType.DPD_CHANGED: DpdChangedPayload,
    EventType.PRODUCT_USAGE_DECLINE: ProductUsageDeclinePayload,
    EventType.BALANCE_DECLINE: BalanceDeclinePayload,
    EventType.INVESTMENT_TRANSFER_INCREASE: InvestmentTransferIncreasePayload,
    EventType.MANUAL_REANALYSIS: ManualReanalysisPayload,
}


def validate_event_payload(event_type: EventType, payload: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize an event payload for the given event type."""
    model_cls = EVENT_PAYLOAD_MODELS.get(event_type)
    if model_cls is None:
        msg = f"Unsupported event type: {event_type}"
        raise ValueError(msg)
    validated = model_cls.model_validate(payload)
    return validated.model_dump(mode="json")
