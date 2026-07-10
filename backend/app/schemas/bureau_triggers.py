"""Bureau trigger API schemas."""

from datetime import date, datetime

from pydantic import Field

from app.models.enums import Severity
from app.schemas.common import APIModel


class BureauTriggerCreate(APIModel):
    """Payload for creating a bureau trigger."""

    customer_id: str = Field(min_length=1, max_length=32)
    product_type: str = Field(min_length=1, max_length=64)
    trigger_type: str = Field(min_length=1, max_length=64)
    institution_category: str = Field(min_length=1, max_length=64)
    amount_band: str = Field(min_length=1, max_length=64)
    severity: Severity
    trigger_date: date
    source: str = Field(min_length=1, max_length=128)
    processed: bool = False


class BureauTriggerUpdate(APIModel):
    """Payload for updating a bureau trigger."""

    severity: Severity | None = None
    processed: bool | None = None


class BureauTriggerSummary(APIModel):
    """Compact bureau trigger representation."""

    bureau_trigger_id: str
    customer_id: str
    product_type: str
    trigger_type: str
    severity: Severity
    trigger_date: date
    processed: bool


class BureauTriggerDetail(APIModel):
    """Full bureau trigger representation."""

    bureau_trigger_id: str
    customer_id: str
    product_type: str
    trigger_type: str
    institution_category: str
    amount_band: str
    severity: Severity
    trigger_date: date
    source: str
    processed: bool
    created_at: datetime
