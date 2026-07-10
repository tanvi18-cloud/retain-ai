"""Transaction feature API schemas."""

from datetime import datetime

from pydantic import Field, field_validator

from app.schemas.common import APIModel, validate_non_negative_amount


class TransactionFeatureCreate(APIModel):
    """Payload for creating transaction features."""

    customer_id: str = Field(min_length=1, max_length=32)
    salary_received_current_month: bool = False
    balance_change_pct_30d: float
    monthly_inflow: float
    monthly_outflow: float
    external_transfer_amount_30d: float
    card_spend_change_pct_30d: float
    forex_spend_30d: float
    competitor_transfer_detected: bool = False
    product_inactivity_days: int = Field(default=0, ge=0)

    @field_validator(
        "monthly_inflow",
        "monthly_outflow",
        "external_transfer_amount_30d",
        "forex_spend_30d",
    )
    @classmethod
    def validate_amounts(cls, value: float) -> float:
        return validate_non_negative_amount(value)


class TransactionFeatureUpdate(APIModel):
    """Payload for updating transaction features."""

    salary_received_current_month: bool | None = None
    balance_change_pct_30d: float | None = None
    monthly_inflow: float | None = None
    monthly_outflow: float | None = None
    external_transfer_amount_30d: float | None = None
    card_spend_change_pct_30d: float | None = None
    forex_spend_30d: float | None = None
    competitor_transfer_detected: bool | None = None
    product_inactivity_days: int | None = Field(default=None, ge=0)


class TransactionFeatureSummary(APIModel):
    """Compact transaction feature representation."""

    transaction_feature_id: str
    customer_id: str
    competitor_transfer_detected: bool
    product_inactivity_days: int


class TransactionFeatureDetail(APIModel):
    """Full transaction feature representation."""

    transaction_feature_id: str
    customer_id: str
    salary_received_current_month: bool
    balance_change_pct_30d: float
    monthly_inflow: float
    monthly_outflow: float
    external_transfer_amount_30d: float
    card_spend_change_pct_30d: float
    forex_spend_30d: float
    competitor_transfer_detected: bool
    product_inactivity_days: int
    last_updated: datetime
