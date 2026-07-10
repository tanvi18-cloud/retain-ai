"""Central configuration for deterministic scoring rules and thresholds."""

from dataclasses import dataclass
from enum import StrEnum


class ChurnRuleCode(StrEnum):
    """Deterministic churn-risk rule identifiers."""

    HIGH_EXTERNAL_PRODUCT_INQUIRY = "HIGH_EXTERNAL_PRODUCT_INQUIRY"
    MEDIUM_EXTERNAL_PRODUCT_INQUIRY = "MEDIUM_EXTERNAL_PRODUCT_INQUIRY"
    LOW_EXTERNAL_PRODUCT_INQUIRY = "LOW_EXTERNAL_PRODUCT_INQUIRY"
    SALARY_CREDIT_STOPPED = "SALARY_CREDIT_STOPPED"
    BALANCE_DROP_OVER_40_PERCENT = "BALANCE_DROP_OVER_40_PERCENT"
    BALANCE_DROP_20_TO_40_PERCENT = "BALANCE_DROP_20_TO_40_PERCENT"
    LARGE_EXTERNAL_TRANSFER = "LARGE_EXTERNAL_TRANSFER"
    COMPETITOR_TRANSFER_DETECTED = "COMPETITOR_TRANSFER_DETECTED"
    CARD_SPEND_DROP_OVER_30_PERCENT = "CARD_SPEND_DROP_OVER_30_PERCENT"
    PRODUCT_INACTIVITY_OVER_30_DAYS = "PRODUCT_INACTIVITY_OVER_30_DAYS"
    MULTIPLE_RECENT_CREDIT_INQUIRIES = "MULTIPLE_RECENT_CREDIT_INQUIRIES"
    FIXED_DEPOSIT_MATURITY_WITH_OUTFLOW = "FIXED_DEPOSIT_MATURITY_WITH_OUTFLOW"
    HIGH_FOREX_SPEND_WITH_TRAVEL_TRIGGER = "HIGH_FOREX_SPEND_WITH_TRAVEL_TRIGGER"
    EXTERNAL_INVESTMENT_TRANSFER_PATTERN = "EXTERNAL_INVESTMENT_TRANSFER_PATTERN"
    RECENT_DPD_DETERIORATION = "RECENT_DPD_DETERIORATION"


class ValueRuleCode(StrEnum):
    """Deterministic customer-value rule identifiers."""

    BALANCE_AND_DEPOSIT_VALUE = "BALANCE_AND_DEPOSIT_VALUE"
    MONTHLY_INFLOW = "MONTHLY_INFLOW"
    ESTIMATED_ANNUAL_VALUE = "ESTIMATED_ANNUAL_VALUE"
    PRODUCT_DEPTH = "PRODUCT_DEPTH"
    RELATIONSHIP_TENURE = "RELATIONSHIP_TENURE"


CHURN_RULE_POINTS: dict[ChurnRuleCode, int] = {
    ChurnRuleCode.HIGH_EXTERNAL_PRODUCT_INQUIRY: 30,
    ChurnRuleCode.MEDIUM_EXTERNAL_PRODUCT_INQUIRY: 20,
    ChurnRuleCode.LOW_EXTERNAL_PRODUCT_INQUIRY: 8,
    ChurnRuleCode.SALARY_CREDIT_STOPPED: 20,
    ChurnRuleCode.BALANCE_DROP_OVER_40_PERCENT: 15,
    ChurnRuleCode.BALANCE_DROP_20_TO_40_PERCENT: 8,
    ChurnRuleCode.LARGE_EXTERNAL_TRANSFER: 15,
    ChurnRuleCode.COMPETITOR_TRANSFER_DETECTED: 10,
    ChurnRuleCode.CARD_SPEND_DROP_OVER_30_PERCENT: 10,
    ChurnRuleCode.PRODUCT_INACTIVITY_OVER_30_DAYS: 8,
    ChurnRuleCode.MULTIPLE_RECENT_CREDIT_INQUIRIES: 10,
    ChurnRuleCode.FIXED_DEPOSIT_MATURITY_WITH_OUTFLOW: 15,
    ChurnRuleCode.HIGH_FOREX_SPEND_WITH_TRAVEL_TRIGGER: 15,
    ChurnRuleCode.EXTERNAL_INVESTMENT_TRANSFER_PATTERN: 15,
    ChurnRuleCode.RECENT_DPD_DETERIORATION: 10,
}

CHURN_SCORE_CAP = 100
VALUE_SCORE_CAP = 100
SCORING_VERSION = "2026.07.1"
ANALYSIS_VERSION = "2026.07.1"

# Churn thresholds (INR unless noted)
LARGE_EXTERNAL_TRANSFER_THRESHOLD = 500_000.0
HIGH_FOREX_SPEND_THRESHOLD = 100_000.0
EXTERNAL_INVESTMENT_TRANSFER_THRESHOLD = 750_000.0
BALANCE_DROP_HIGH_THRESHOLD = -40.0
BALANCE_DROP_MEDIUM_THRESHOLD = -20.0
CARD_SPEND_DROP_THRESHOLD = -30.0
PRODUCT_INACTIVITY_DAYS_THRESHOLD = 30
MULTIPLE_CREDIT_INQUIRIES_THRESHOLD = 2
RECENT_DPD_DETERIORATION_THRESHOLD = 30
FD_MATURITY_DAYS_WINDOW = 90

# Score bands
CHURN_BAND_LOW_MAX = 29
CHURN_BAND_MEDIUM_MAX = 49
CHURN_BAND_HIGH_MAX = 69

VALUE_BAND_LOW_MAX = 29
VALUE_BAND_MEDIUM_MAX = 49
VALUE_BAND_HIGH_MAX = 69

# Priority decision bands
DECISION_RETAIN_MIN = 70
DECISION_REVIEW_MIN = 50
DECISION_MONITOR_MIN = 30

DEFAULT_CHURN_PRIORITY_WEIGHT = 0.55
DEFAULT_VALUE_PRIORITY_WEIGHT = 0.45

# Value component caps
VALUE_BALANCE_MAX_POINTS = 35
VALUE_INFLOW_MAX_POINTS = 20
VALUE_EAV_MAX_POINTS = 20
VALUE_PRODUCT_DEPTH_MAX_POINTS = 15
VALUE_TENURE_MAX_POINTS = 10


@dataclass(frozen=True)
class ValueBracket:
    """Numeric bracket for value scoring."""

    minimum: float
    points: float


BALANCE_VALUE_BRACKETS: tuple[ValueBracket, ...] = (
    ValueBracket(minimum=2_500_000, points=35),
    ValueBracket(minimum=1_000_000, points=28),
    ValueBracket(minimum=500_000, points=22),
    ValueBracket(minimum=250_000, points=16),
    ValueBracket(minimum=100_000, points=10),
    ValueBracket(minimum=50_000, points=5),
)

INFLOW_VALUE_BRACKETS: tuple[ValueBracket, ...] = (
    ValueBracket(minimum=250_000, points=20),
    ValueBracket(minimum=150_000, points=16),
    ValueBracket(minimum=100_000, points=12),
    ValueBracket(minimum=75_000, points=8),
    ValueBracket(minimum=50_000, points=4),
)

EAV_VALUE_BRACKETS: tuple[ValueBracket, ...] = (
    ValueBracket(minimum=1_500_000, points=20),
    ValueBracket(minimum=1_000_000, points=16),
    ValueBracket(minimum=750_000, points=12),
    ValueBracket(minimum=500_000, points=8),
    ValueBracket(minimum=250_000, points=4),
)

PRODUCT_DEPTH_BRACKETS: tuple[ValueBracket, ...] = (
    ValueBracket(minimum=4, points=15),
    ValueBracket(minimum=3, points=12),
    ValueBracket(minimum=2, points=8),
    ValueBracket(minimum=1, points=4),
)

TENURE_YEARS_BRACKETS: tuple[ValueBracket, ...] = (
    ValueBracket(minimum=10, points=10),
    ValueBracket(minimum=7, points=8),
    ValueBracket(minimum=5, points=6),
    ValueBracket(minimum=3, points=4),
    ValueBracket(minimum=1, points=2),
)


def bracket_points(value: float, brackets: tuple[ValueBracket, ...]) -> float:
    """Return points for the highest matching bracket."""
    for bracket in brackets:
        if value >= bracket.minimum:
            return bracket.points
    return 0.0
