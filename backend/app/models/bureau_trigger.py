"""Credit bureau trigger events."""

from datetime import date

from sqlmodel import Field, SQLModel

from app.models.base import CreatedAtMixin, new_uuid
from app.models.enums import Severity


class BureauTrigger(CreatedAtMixin, SQLModel, table=True):
    """External bureau signal indicating potential customer risk or opportunity."""

    __tablename__ = "bureau_triggers"

    id: str = Field(default_factory=new_uuid, primary_key=True, max_length=36)
    customer_id: str = Field(
        foreign_key="customers.customer_id",
        nullable=False,
        index=True,
        max_length=32,
    )
    product_type: str = Field(max_length=64, nullable=False)
    trigger_type: str = Field(max_length=64, nullable=False)
    institution_category: str = Field(max_length=64, nullable=False)
    amount_band: str = Field(max_length=64, nullable=False)
    severity: Severity = Field(nullable=False, index=True)
    trigger_date: date = Field(nullable=False)
    source: str = Field(max_length=128, nullable=False)
    processed: bool = Field(default=False, nullable=False)
