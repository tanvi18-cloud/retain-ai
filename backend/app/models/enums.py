"""Central enum definitions for database models."""

from enum import StrEnum


class CustomerSegment(StrEnum):
    """Retail banking customer segment."""

    STANDARD = "STANDARD"
    MASS_AFFLUENT = "MASS_AFFLUENT"
    PRIORITY = "PRIORITY"
    PRIVATE = "PRIVATE"


class PreferredChannel(StrEnum):
    """Customer-preferred communication channel."""

    EMAIL = "EMAIL"
    PHONE = "PHONE"
    SMS = "SMS"


class Severity(StrEnum):
    """Severity level for triggers and alerts."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RecommendationDecision(StrEnum):
    """Retention decision outcome for a customer recommendation."""

    RETAIN = "RETAIN"
    REVIEW = "REVIEW"
    MONITOR = "MONITOR"
    NO_ACTION = "NO_ACTION"


class RecommendationStatus(StrEnum):
    """Workflow status for a retention recommendation."""

    NEW = "NEW"
    REVIEWED = "REVIEWED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CONTACTED = "CONTACTED"
    CLOSED = "CLOSED"


class IncomingEventStatus(StrEnum):
    """Processing status for an inbound customer event."""

    RECEIVED = "RECEIVED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class EventType(StrEnum):
    """Supported inbound event types for async processing."""

    EXTERNAL_HOME_LOAN_INQUIRY = "EXTERNAL_HOME_LOAN_INQUIRY"
    EXTERNAL_CARD_INQUIRY = "EXTERNAL_CARD_INQUIRY"
    SALARY_CREDIT_STOPPED = "SALARY_CREDIT_STOPPED"
    SALARY_CREDIT_RESUMED = "SALARY_CREDIT_RESUMED"
    LARGE_EXTERNAL_TRANSFER = "LARGE_EXTERNAL_TRANSFER"
    FIXED_DEPOSIT_MATURITY = "FIXED_DEPOSIT_MATURITY"
    FOREX_SPEND_INCREASE = "FOREX_SPEND_INCREASE"
    DPD_CHANGED = "DPD_CHANGED"
    PRODUCT_USAGE_DECLINE = "PRODUCT_USAGE_DECLINE"
    BALANCE_DECLINE = "BALANCE_DECLINE"
    INVESTMENT_TRANSFER_INCREASE = "INVESTMENT_TRANSFER_INCREASE"
    MANUAL_REANALYSIS = "MANUAL_REANALYSIS"


class AlertType(StrEnum):
    """Alert classification."""

    RULES_PREVIEW = "RULES_PREVIEW"
    AGENT_RECOMMENDATION = "AGENT_RECOMMENDATION"
    SYSTEM = "SYSTEM"


class NotificationStatus(StrEnum):
    """Delivery status for alert notifications."""

    PENDING = "PENDING"
    SENT = "SENT"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    NOT_REQUIRED = "NOT_REQUIRED"


class FreshnessStatus(StrEnum):
    """Freshness state for an aggregated Customer 360 data source."""

    FRESH = "FRESH"
    STALE = "STALE"
    MISSING = "MISSING"


class AnalysisExecutionMode(StrEnum):
    """Analysis execution mode."""

    RULES_ONLY = "RULES_ONLY"
    AGENTIC = "AGENTIC"


class AnalysisExecutionStatus(StrEnum):
    """Analysis execution lifecycle status."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CreatedByMode(StrEnum):
    """Origin mode for a persisted recommendation."""

    MOCK = "MOCK"
    QWEN = "QWEN"
    RULES_ONLY = "RULES_ONLY"


class ChatIntent(StrEnum):
    """Supported RM copilot chat intents."""

    CUSTOMER_RISK_EXPLANATION = "CUSTOMER_RISK_EXPLANATION"
    CUSTOMER_OFFER_EXPLANATION = "CUSTOMER_OFFER_EXPLANATION"
    CUSTOMER_ELIGIBILITY_EXPLANATION = "CUSTOMER_ELIGIBILITY_EXPLANATION"
    CUSTOMER_COMPARISON = "CUSTOMER_COMPARISON"
    PRIORITY_CUSTOMER_LIST = "PRIORITY_CUSTOMER_LIST"
    PORTFOLIO_SUMMARY = "PORTFOLIO_SUMMARY"
    TRIGGER_SEARCH = "TRIGGER_SEARCH"
    REVENUE_AT_RISK = "REVENUE_AT_RISK"
    RM_TALKING_POINTS = "RM_TALKING_POINTS"
    RECOMMENDATION_STATUS = "RECOMMENDATION_STATUS"
    DATA_FRESHNESS = "DATA_FRESHNESS"
    DPD_EXPLANATION = "DPD_EXPLANATION"
    FOLLOW_UP_QUESTION = "FOLLOW_UP_QUESTION"
    GENERAL_HELP = "GENERAL_HELP"
    UNSUPPORTED = "UNSUPPORTED"


class ChatConversationStatus(StrEnum):
    """Lifecycle status for an RM chat conversation."""

    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


class ChatMessageRole(StrEnum):
    """Role of a persisted chat message."""

    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"
