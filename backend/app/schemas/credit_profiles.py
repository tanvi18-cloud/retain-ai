"""Credit profile API schemas."""

from datetime import datetime

from pydantic import Field, field_validator

from app.schemas.common import APIModel, validate_score


class CreditProfileCreate(APIModel):
    """Payload for creating a credit profile."""

    customer_id: str = Field(min_length=1, max_length=32)
    credit_score: int
    max_dpd_12m: int = Field(ge=0)
    credit_utilization_pct: float
    active_loans: int = Field(default=0, ge=0)
    recent_credit_inquiries: int = Field(default=0, ge=0)
    default_flag: bool = False

    @field_validator("credit_score")
    @classmethod
    def validate_credit_score(cls, value: int) -> int:
        validate_score(float(value))
        return value

    @field_validator("credit_utilization_pct")
    @classmethod
    def validate_utilization(cls, value: float) -> float:
        validate_score(value)
        return value


class CreditProfileUpdate(APIModel):
    """Payload for updating a credit profile."""

    credit_score: int | None = None
    max_dpd_12m: int | None = Field(default=None, ge=0)
    credit_utilization_pct: float | None = None
    active_loans: int | None = Field(default=None, ge=0)
    recent_credit_inquiries: int | None = Field(default=None, ge=0)
    default_flag: bool | None = None


class CreditProfileSummary(APIModel):
    """Compact credit profile representation."""

    credit_profile_id: str
    customer_id: str
    credit_score: int
    default_flag: bool


class CreditProfileDetail(APIModel):
    """Full credit profile representation."""

    credit_profile_id: str
    customer_id: str
    credit_score: int
    max_dpd_12m: int
    credit_utilization_pct: float
    active_loans: int
    recent_credit_inquiries: int
    default_flag: bool
    last_updated: datetime
