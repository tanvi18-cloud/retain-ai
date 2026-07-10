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
