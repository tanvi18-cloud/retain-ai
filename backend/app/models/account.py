"""Customer account records."""

from datetime import date

from sqlmodel import Field, SQLModel

from app.models.base import TimestampMixin, new_uuid


class Account(TimestampMixin, SQLModel, table=True):
    """Bank account linked to a customer."""

    __tablename__ = "accounts"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=36)
    customer_id: str = Field(
        foreign_key="customers.customer_id",
        nullable=False,
        index=True,
        max_length=32,
    )
    account_type: str = Field(max_length=64, nullable=False)
    current_balance: float = Field(nullable=False)
    average_balance_90d: float = Field(nullable=False)
    salary_account: bool = Field(default=False, nullable=False)
    status: str = Field(max_length=32, nullable=False, index=True)
    fixed_deposit_maturity_date: date | None = Field(default=None, nullable=True)
