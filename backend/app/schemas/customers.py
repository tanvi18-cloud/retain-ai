"""Customer API schemas."""

from datetime import date, datetime

from pydantic import Field, field_validator

from app.models.enums import CustomerSegment, PreferredChannel
from app.schemas.common import APIModel, validate_email_address, validate_non_negative_amount


class CustomerCreate(APIModel):
    """Payload for creating a customer."""

    customer_id: str = Field(min_length=1, max_length=32)
    full_name: str = Field(min_length=1, max_length=255)
    segment: CustomerSegment
    relationship_start_date: date
    assigned_rm_id: str = Field(min_length=1, max_length=64)
    assigned_rm_name: str = Field(min_length=1, max_length=255)
    assigned_rm_email: str = Field(min_length=1, max_length=255)
    communication_consent: bool = True
    preferred_channel: PreferredChannel
    estimated_annual_value: float

    @field_validator("assigned_rm_email")
    @classmethod
    def validate_rm_email(cls, value: str) -> str:
        return validate_email_address(value)

    @field_validator("estimated_annual_value")
    @classmethod
    def validate_value(cls, value: float) -> float:
        return validate_non_negative_amount(value)


class CustomerUpdate(APIModel):
    """Payload for updating mutable customer fields."""

    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    segment: CustomerSegment | None = None
    assigned_rm_id: str | None = Field(default=None, min_length=1, max_length=64)
    assigned_rm_name: str | None = Field(default=None, min_length=1, max_length=255)
    assigned_rm_email: str | None = Field(default=None, min_length=1, max_length=255)
    communication_consent: bool | None = None
    preferred_channel: PreferredChannel | None = None
    estimated_annual_value: float | None = None

    @field_validator("assigned_rm_email")
    @classmethod
    def validate_rm_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_email_address(value)

    @field_validator("estimated_annual_value")
    @classmethod
    def validate_value(cls, value: float | None) -> float | None:
        if value is None:
            return None
        return validate_non_negative_amount(value)


class CustomerSummary(APIModel):
    """Compact customer representation for list views."""

    customer_id: str
    full_name: str
    segment: CustomerSegment
    assigned_rm_name: str
    estimated_annual_value: float
    preferred_channel: PreferredChannel


class CustomerDetail(APIModel):
    """Full customer profile for detail views."""

    customer_id: str
    full_name: str
    segment: CustomerSegment
    relationship_start_date: date
    assigned_rm_id: str
    assigned_rm_name: str
    assigned_rm_email: str
    communication_consent: bool
    preferred_channel: PreferredChannel
    estimated_annual_value: float
    created_at: datetime
    updated_at: datetime

    @field_validator("assigned_rm_email")
    @classmethod
    def validate_rm_email(cls, value: str) -> str:
        return validate_email_address(value)
