"""Transaction feature persistence operations."""

from sqlmodel import Session, select

from app.models.transaction_feature import TransactionFeature
from app.schemas.transaction_features import TransactionFeatureDetail


def _to_detail(feature: TransactionFeature) -> TransactionFeatureDetail:
    return TransactionFeatureDetail(
        transaction_feature_id=feature.id,
        customer_id=feature.customer_id,
        salary_received_current_month=feature.salary_received_current_month,
        balance_change_pct_30d=feature.balance_change_pct_30d,
        monthly_inflow=feature.monthly_inflow,
        monthly_outflow=feature.monthly_outflow,
        external_transfer_amount_30d=feature.external_transfer_amount_30d,
        card_spend_change_pct_30d=feature.card_spend_change_pct_30d,
        forex_spend_30d=feature.forex_spend_30d,
        competitor_transfer_detected=feature.competitor_transfer_detected,
        product_inactivity_days=feature.product_inactivity_days,
        last_updated=feature.last_updated,
    )


class TransactionFeatureRepository:
    """Data access for customer transaction features."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_customer(self, customer_id: str) -> TransactionFeatureDetail | None:
        """Return transaction features for a customer when present."""
        statement = select(TransactionFeature).where(
            TransactionFeature.customer_id == customer_id
        )
        feature = self.session.exec(statement).first()
        if feature is None:
            return None
        return _to_detail(feature)
