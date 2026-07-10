"""Credit profile persistence operations."""

from sqlmodel import Session, select

from app.models.credit_profile import CreditProfile
from app.schemas.credit_profiles import CreditProfileDetail


def _to_detail(profile: CreditProfile) -> CreditProfileDetail:
    return CreditProfileDetail(
        credit_profile_id=profile.id,
        customer_id=profile.customer_id,
        credit_score=profile.credit_score,
        max_dpd_12m=profile.max_dpd_12m,
        credit_utilization_pct=profile.credit_utilization_pct,
        active_loans=profile.active_loans,
        recent_credit_inquiries=profile.recent_credit_inquiries,
        default_flag=profile.default_flag,
        last_updated=profile.last_updated,
    )


class CreditProfileRepository:
    """Data access for customer credit profiles."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_customer(self, customer_id: str) -> CreditProfileDetail | None:
        """Return the credit profile for a customer when present."""
        statement = select(CreditProfile).where(CreditProfile.customer_id == customer_id)
        profile = self.session.exec(statement).first()
        if profile is None:
            return None
        return _to_detail(profile)
