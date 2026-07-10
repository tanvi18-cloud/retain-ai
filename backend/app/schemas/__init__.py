"""Public API schema exports."""

from app.schemas.alerts import AlertCreate, AlertDetail, AlertSummary, AlertUpdate
from app.schemas.common import ApiError, ApiErrorResponse, PaginatedResponse, PaginationParams
from app.schemas.customer_360 import Customer360Response
from app.schemas.customers import CustomerCreate, CustomerDetail, CustomerSummary, CustomerUpdate
from app.schemas.health import HealthResponse
from app.schemas.offers import OfferCreate, OfferDetail, OfferSummary, OfferUpdate
from app.schemas.recommendations import (
    RecommendationCreate,
    RecommendationDetail,
    RecommendationSummary,
    RecommendationUpdate,
)

__all__ = [
    "AlertCreate",
    "AlertDetail",
    "AlertSummary",
    "AlertUpdate",
    "ApiError",
    "ApiErrorResponse",
    "Customer360Response",
    "CustomerCreate",
    "CustomerDetail",
    "CustomerSummary",
    "CustomerUpdate",
    "HealthResponse",
    "OfferCreate",
    "OfferDetail",
    "OfferSummary",
    "OfferUpdate",
    "PaginatedResponse",
    "PaginationParams",
    "RecommendationCreate",
    "RecommendationDetail",
    "RecommendationSummary",
    "RecommendationUpdate",
]
