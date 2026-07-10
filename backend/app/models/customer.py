"""Customer master record."""

from datetime import date

from sqlmodel import Field, SQLModel

from app.models.base import TimestampMixin
from app.models.enums import CustomerSegment, PreferredChannel


class Customer(TimestampMixin, SQLModel, table=True):
    """Synthetic retail banking customer profile."""

    __tablename__ = "customers"

    customer_id: str = Field(primary_key=True, max_length=32)
    full_name: str = Field(max_length=255, nullable=False)
    segment: CustomerSegment = Field(nullable=False)
    relationship_start_date: date = Field(nullable=False)
    assigned_rm_id: str = Field(max_length=64, nullable=False)
    assigned_rm_name: str = Field(max_length=255, nullable=False)
    assigned_rm_email: str = Field(max_length=255, nullable=False)
    communication_consent: bool = Field(default=True, nullable=False)
    preferred_channel: PreferredChannel = Field(nullable=False)
    estimated_annual_value: float = Field(nullable=False)
