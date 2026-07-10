"""Customer 360 composite API schema."""

from app.schemas.accounts import AccountSummary
from app.schemas.alerts import AlertSummary
from app.schemas.bureau_triggers import BureauTriggerSummary
from app.schemas.common import APIModel
from app.schemas.credit_profiles import CreditProfileDetail
from app.schemas.customers import CustomerDetail
from app.schemas.events import IncomingEventSummary
from app.schemas.interactions import InteractionSummary
from app.schemas.recommendations import RecommendationSummary
from app.schemas.transaction_features import TransactionFeatureDetail


class Customer360Response(APIModel):
    """Aggregated customer view for RM dashboards."""

    customer: CustomerDetail
    accounts: list[AccountSummary]
    credit_profile: CreditProfileDetail | None
    transaction_features: TransactionFeatureDetail | None
    bureau_triggers: list[BureauTriggerSummary]
    recommendations: list[RecommendationSummary]
    alerts: list[AlertSummary]
    interactions: list[InteractionSummary]
    events: list[IncomingEventSummary]
