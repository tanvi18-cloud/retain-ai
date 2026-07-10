"""Aggregated transaction behavior features."""

from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.base import new_uuid, utc_now


class TransactionFeature(SQLModel, table=True):
    """Derived transaction and engagement features for retention scoring."""

    __tablename__ = "transaction_features"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=36)
    customer_id: str = Field(
        foreign_key="customers.customer_id",
        nullable=False,
        unique=True,
        index=True,
        max_length=32,
    )
    salary_received_current_month: bool = Field(default=False, nullable=False)
    balance_change_pct_30d: float = Field(nullable=False)
    monthly_inflow: float = Field(nullable=False)
    monthly_outflow: float = Field(nullable=False)
    external_transfer_amount_30d: float = Field(nullable=False)
    card_spend_change_pct_30d: float = Field(nullable=False)
    forex_spend_30d: float = Field(nullable=False)
    competitor_transfer_detected: bool = Field(default=False, nullable=False)
    product_inactivity_days: int = Field(default=0, nullable=False)
    last_updated: datetime = Field(default_factory=utc_now, nullable=False)
