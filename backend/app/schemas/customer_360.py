"""Customer 360 composite API schemas."""

from datetime import datetime

from app.models.enums import FreshnessStatus
from app.schemas.accounts import AccountDetail
from app.schemas.bureau_triggers import BureauTriggerDetail
from app.schemas.common import APIModel
from app.schemas.credit_profiles import CreditProfileDetail
from app.schemas.customers import CustomerDetail
from app.schemas.interactions import InteractionDetail
from app.schemas.recommendations import RecommendationSummary
from app.schemas.transaction_features import TransactionFeatureDetail


class DataFreshnessSource(APIModel):
    """Freshness metadata for a single Customer 360 data source."""

    last_updated: datetime | None
    status: FreshnessStatus


class Customer360DataFreshness(APIModel):
    """Freshness metadata across Customer 360 source systems."""

    core_banking: DataFreshnessSource
    credit_history: DataFreshnessSource
    bureau_triggers: DataFreshnessSource
    transaction_history: DataFreshnessSource


class Customer360Response(APIModel):
    """Aggregated customer view for RM dashboards."""

    customer: CustomerDetail
    accounts: list[AccountDetail]
    credit_profile: CreditProfileDetail | None
    bureau_triggers: list[BureauTriggerDetail]
    transaction_features: TransactionFeatureDetail | None
    recommendations: list[RecommendationSummary]
    interactions: list[InteractionDetail]
    data_freshness: Customer360DataFreshness
    data_warnings: list[str]
