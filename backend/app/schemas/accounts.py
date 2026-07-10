"""Account API schemas."""

from datetime import date, datetime

from pydantic import Field, field_validator

from app.schemas.common import APIModel, validate_non_negative_amount


class AccountCreate(APIModel):
    """Payload for creating an account."""

    customer_id: str = Field(min_length=1, max_length=32)
    account_type: str = Field(min_length=1, max_length=64)
    current_balance: float
    average_balance_90d: float
    salary_account: bool = False
    status: str = Field(min_length=1, max_length=32)
    fixed_deposit_maturity_date: date | None = None

    @field_validator("current_balance", "average_balance_90d")
    @classmethod
    def validate_amounts(cls, value: float) -> float:
        return validate_non_negative_amount(value)


class AccountUpdate(APIModel):
    """Payload for updating an account."""

    current_balance: float | None = None
    average_balance_90d: float | None = None
    salary_account: bool | None = None
    status: str | None = Field(default=None, min_length=1, max_length=32)
    fixed_deposit_maturity_date: date | None = None


class AccountSummary(APIModel):
    """Compact account representation."""

    account_id: str
    customer_id: str
    account_type: str
    current_balance: float
    status: str
    salary_account: bool


class AccountDetail(APIModel):
    """Full account representation."""

    account_id: str
    customer_id: str
    account_type: str
    current_balance: float
    average_balance_90d: float
    salary_account: bool
    status: str
    fixed_deposit_maturity_date: date | None
    created_at: datetime
    updated_at: datetime
