"""Customer credit profile snapshot."""

from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.base import new_uuid, utc_now


class CreditProfile(SQLModel, table=True):
    """Credit bureau and internal credit metrics for a customer."""

    __tablename__ = "credit_profiles"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=36)
    customer_id: str = Field(
        foreign_key="customers.customer_id",
        nullable=False,
        unique=True,
        index=True,
        max_length=32,
    )
    credit_score: int = Field(nullable=False)
    max_dpd_12m: int = Field(nullable=False)
    credit_utilization_pct: float = Field(nullable=False)
    active_loans: int = Field(default=0, nullable=False)
    recent_credit_inquiries: int = Field(default=0, nullable=False)
    default_flag: bool = Field(default=False, nullable=False)
    last_updated: datetime = Field(default_factory=utc_now, nullable=False)
