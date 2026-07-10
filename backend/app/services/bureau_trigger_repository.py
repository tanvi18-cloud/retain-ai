"""Bureau trigger persistence operations."""

from sqlmodel import Session, select

from app.models.bureau_trigger import BureauTrigger
from app.schemas.bureau_triggers import BureauTriggerDetail


def _to_detail(trigger: BureauTrigger) -> BureauTriggerDetail:
    return BureauTriggerDetail(
        bureau_trigger_id=trigger.id,
        customer_id=trigger.customer_id,
        product_type=trigger.product_type,
        trigger_type=trigger.trigger_type,
        institution_category=trigger.institution_category,
        amount_band=trigger.amount_band,
        severity=trigger.severity,
        trigger_date=trigger.trigger_date,
        source=trigger.source,
        processed=trigger.processed,
        created_at=trigger.created_at,
    )


class BureauTriggerRepository:
    """Data access for bureau trigger records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def list_by_customer(self, customer_id: str) -> list[BureauTriggerDetail]:
        """Return bureau triggers for a customer ordered newest first."""
        statement = (
            select(BureauTrigger)
            .where(BureauTrigger.customer_id == customer_id)
            .order_by(BureauTrigger.trigger_date.desc(), BureauTrigger.created_at.desc())
        )
        triggers = self.session.exec(statement).all()
        return [_to_detail(trigger) for trigger in triggers]
