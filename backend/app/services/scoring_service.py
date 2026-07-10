"""Deterministic churn, value, and priority scoring service."""

from __future__ import annotations

from datetime import UTC, date, datetime

from app.core.config import Settings, get_settings
from app.core.scoring_rules import (
    BALANCE_DROP_HIGH_THRESHOLD,
    BALANCE_DROP_MEDIUM_THRESHOLD,
    BALANCE_VALUE_BRACKETS,
    CARD_SPEND_DROP_THRESHOLD,
    CHURN_BAND_HIGH_MAX,
    CHURN_BAND_LOW_MAX,
    CHURN_BAND_MEDIUM_MAX,
    CHURN_RULE_POINTS,
    CHURN_SCORE_CAP,
    DECISION_RETAIN_MIN,
    DECISION_REVIEW_MIN,
    EAV_VALUE_BRACKETS,
    EXTERNAL_INVESTMENT_TRANSFER_THRESHOLD,
    FD_MATURITY_DAYS_WINDOW,
    HIGH_FOREX_SPEND_THRESHOLD,
    INFLOW_VALUE_BRACKETS,
    LARGE_EXTERNAL_TRANSFER_THRESHOLD,
    MULTIPLE_CREDIT_INQUIRIES_THRESHOLD,
    PRODUCT_DEPTH_BRACKETS,
    PRODUCT_INACTIVITY_DAYS_THRESHOLD,
    RECENT_DPD_DETERIORATION_THRESHOLD,
    SCORING_VERSION,
    TENURE_YEARS_BRACKETS,
    VALUE_BALANCE_MAX_POINTS,
    VALUE_BAND_HIGH_MAX,
    VALUE_BAND_LOW_MAX,
    VALUE_BAND_MEDIUM_MAX,
    VALUE_EAV_MAX_POINTS,
    VALUE_INFLOW_MAX_POINTS,
    VALUE_PRODUCT_DEPTH_MAX_POINTS,
    VALUE_SCORE_CAP,
    VALUE_TENURE_MAX_POINTS,
    ChurnRuleCode,
    ValueRuleCode,
    bracket_points,
)
from app.models.enums import RecommendationDecision, Severity
from app.schemas.customer_360 import Customer360Response
from app.schemas.scoring import PriorityResult, RuleContribution, ScoreBand, ScoreResult


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _score_band(score: int, *, low_max: int, medium_max: int, high_max: int) -> ScoreBand:
    if score <= low_max:
        return ScoreBand.LOW
    if score <= medium_max:
        return ScoreBand.MEDIUM
    if score <= high_max:
        return ScoreBand.HIGH
    return ScoreBand.CRITICAL


def _churn_band(score: int) -> ScoreBand:
    return _score_band(
        score,
        low_max=CHURN_BAND_LOW_MAX,
        medium_max=CHURN_BAND_MEDIUM_MAX,
        high_max=CHURN_BAND_HIGH_MAX,
    )


def _value_band(score: int) -> ScoreBand:
    return _score_band(
        score,
        low_max=VALUE_BAND_LOW_MAX,
        medium_max=VALUE_BAND_MEDIUM_MAX,
        high_max=VALUE_BAND_HIGH_MAX,
    )


def _contribution(
    *,
    rule_code: str,
    description: str,
    points: float,
    observed_value: object,
    source_system: str,
    triggered: bool,
    source_reference: str | None = None,
) -> RuleContribution:
    return RuleContribution(
        rule_code=rule_code,
        description=description,
        points=points if triggered else 0,
        observed_value=observed_value,
        source_system=source_system,
        source_reference=source_reference,
        triggered=triggered,
    )


class ScoringService:
    """Calculate deterministic retention scores."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def calculate_churn_risk(
        self,
        customer_360: Customer360Response,
        *,
        include_untriggered: bool = False,
    ) -> ScoreResult:
        """Calculate explainable churn risk from Customer 360 data."""
        contributions: list[RuleContribution] = []
        total = 0.0
        triggers = customer_360.bureau_triggers
        features = customer_360.transaction_features
        credit = customer_360.credit_profile
        accounts = customer_360.accounts

        high_inquiry = any(
            t.trigger_type == "EXTERNAL_INQUIRY"
            and t.severity in {Severity.HIGH, Severity.CRITICAL}
            for t in triggers
        )
        medium_inquiry = any(
            t.trigger_type == "EXTERNAL_INQUIRY" and t.severity == Severity.MEDIUM for t in triggers
        )
        low_inquiry = any(
            t.trigger_type == "EXTERNAL_INQUIRY" and t.severity == Severity.LOW for t in triggers
        )

        for code, triggered in (
            (ChurnRuleCode.HIGH_EXTERNAL_PRODUCT_INQUIRY, high_inquiry),
            (ChurnRuleCode.MEDIUM_EXTERNAL_PRODUCT_INQUIRY, medium_inquiry and not high_inquiry),
            (
                ChurnRuleCode.LOW_EXTERNAL_PRODUCT_INQUIRY,
                low_inquiry and not high_inquiry and not medium_inquiry,
            ),
        ):
            points = CHURN_RULE_POINTS[code]
            contribution = _contribution(
                rule_code=code.value,
                description=code.value.replace("_", " ").title(),
                points=points,
                observed_value=triggered,
                source_system="CREDIT_BUREAU",
                triggered=triggered,
            )
            if triggered or include_untriggered:
                contributions.append(contribution)
            if triggered:
                total += points

        salary_stopped = features is not None and not features.salary_received_current_month
        contribution = _contribution(
            rule_code=ChurnRuleCode.SALARY_CREDIT_STOPPED.value,
            description="Salary credit not received in current month",
            points=CHURN_RULE_POINTS[ChurnRuleCode.SALARY_CREDIT_STOPPED],
            observed_value=None if features is None else features.salary_received_current_month,
            source_system="TRANSACTION_ENGINE",
            triggered=salary_stopped,
        )
        if salary_stopped or include_untriggered:
            contributions.append(contribution)
        if salary_stopped:
            total += CHURN_RULE_POINTS[ChurnRuleCode.SALARY_CREDIT_STOPPED]

        balance_change = features.balance_change_pct_30d if features else None
        drop_high = balance_change is not None and balance_change <= BALANCE_DROP_HIGH_THRESHOLD
        drop_medium = (
            balance_change is not None
            and BALANCE_DROP_HIGH_THRESHOLD < balance_change <= BALANCE_DROP_MEDIUM_THRESHOLD
        )
        for code, triggered, observed in (
            (ChurnRuleCode.BALANCE_DROP_OVER_40_PERCENT, drop_high, balance_change),
            (ChurnRuleCode.BALANCE_DROP_20_TO_40_PERCENT, drop_medium, balance_change),
        ):
            points = CHURN_RULE_POINTS[code]
            contribution = _contribution(
                rule_code=code.value,
                description=code.value.replace("_", " ").title(),
                points=points,
                observed_value=observed,
                source_system="TRANSACTION_ENGINE",
                triggered=triggered,
            )
            if triggered or include_untriggered:
                contributions.append(contribution)
            if triggered:
                total += points

        external_transfer = features.external_transfer_amount_30d if features else None
        large_transfer = (
            external_transfer is not None and external_transfer >= LARGE_EXTERNAL_TRANSFER_THRESHOLD
        )
        contribution = _contribution(
            rule_code=ChurnRuleCode.LARGE_EXTERNAL_TRANSFER.value,
            description="Large external transfer in last 30 days",
            points=CHURN_RULE_POINTS[ChurnRuleCode.LARGE_EXTERNAL_TRANSFER],
            observed_value=external_transfer,
            source_system="TRANSACTION_ENGINE",
            triggered=large_transfer,
        )
        if large_transfer or include_untriggered:
            contributions.append(contribution)
        if large_transfer:
            total += CHURN_RULE_POINTS[ChurnRuleCode.LARGE_EXTERNAL_TRANSFER]

        competitor = features.competitor_transfer_detected if features else False
        if features is None:
            competitor = False
        contribution = _contribution(
            rule_code=ChurnRuleCode.COMPETITOR_TRANSFER_DETECTED.value,
            description="Competitor transfer pattern detected",
            points=CHURN_RULE_POINTS[ChurnRuleCode.COMPETITOR_TRANSFER_DETECTED],
            observed_value=None if features is None else features.competitor_transfer_detected,
            source_system="TRANSACTION_ENGINE",
            triggered=competitor,
        )
        if competitor or include_untriggered:
            contributions.append(contribution)
        if competitor:
            total += CHURN_RULE_POINTS[ChurnRuleCode.COMPETITOR_TRANSFER_DETECTED]

        card_drop = (
            features is not None and features.card_spend_change_pct_30d <= CARD_SPEND_DROP_THRESHOLD
        )
        contribution = _contribution(
            rule_code=ChurnRuleCode.CARD_SPEND_DROP_OVER_30_PERCENT.value,
            description="Card spend dropped more than 30 percent",
            points=CHURN_RULE_POINTS[ChurnRuleCode.CARD_SPEND_DROP_OVER_30_PERCENT],
            observed_value=None if features is None else features.card_spend_change_pct_30d,
            source_system="TRANSACTION_ENGINE",
            triggered=card_drop,
        )
        if card_drop or include_untriggered:
            contributions.append(contribution)
        if card_drop:
            total += CHURN_RULE_POINTS[ChurnRuleCode.CARD_SPEND_DROP_OVER_30_PERCENT]

        inactivity = (
            features is not None
            and features.product_inactivity_days > PRODUCT_INACTIVITY_DAYS_THRESHOLD
        )
        contribution = _contribution(
            rule_code=ChurnRuleCode.PRODUCT_INACTIVITY_OVER_30_DAYS.value,
            description="Product inactivity exceeds 30 days",
            points=CHURN_RULE_POINTS[ChurnRuleCode.PRODUCT_INACTIVITY_OVER_30_DAYS],
            observed_value=None if features is None else features.product_inactivity_days,
            source_system="TRANSACTION_ENGINE",
            triggered=inactivity,
        )
        if inactivity or include_untriggered:
            contributions.append(contribution)
        if inactivity:
            total += CHURN_RULE_POINTS[ChurnRuleCode.PRODUCT_INACTIVITY_OVER_30_DAYS]

        inquiries = credit.recent_credit_inquiries if credit else None
        multiple_inquiries = (
            inquiries is not None and inquiries >= MULTIPLE_CREDIT_INQUIRIES_THRESHOLD
        )
        contribution = _contribution(
            rule_code=ChurnRuleCode.MULTIPLE_RECENT_CREDIT_INQUIRIES.value,
            description="Multiple recent credit inquiries",
            points=CHURN_RULE_POINTS[ChurnRuleCode.MULTIPLE_RECENT_CREDIT_INQUIRIES],
            observed_value=inquiries,
            source_system="CREDIT_BUREAU",
            triggered=multiple_inquiries,
        )
        if multiple_inquiries or include_untriggered:
            contributions.append(contribution)
        if multiple_inquiries:
            total += CHURN_RULE_POINTS[ChurnRuleCode.MULTIPLE_RECENT_CREDIT_INQUIRIES]

        today = date.today()
        fd_maturity_soon = any(
            account.fixed_deposit_maturity_date is not None
            and 0 <= (account.fixed_deposit_maturity_date - today).days <= FD_MATURITY_DAYS_WINDOW
            for account in accounts
        )
        fd_outflow = fd_maturity_soon and (
            large_transfer or (balance_change is not None and balance_change < 0)
        )
        contribution = _contribution(
            rule_code=ChurnRuleCode.FIXED_DEPOSIT_MATURITY_WITH_OUTFLOW.value,
            description="Fixed deposit maturity with outflow pattern",
            points=CHURN_RULE_POINTS[ChurnRuleCode.FIXED_DEPOSIT_MATURITY_WITH_OUTFLOW],
            observed_value={
                "fd_maturity_soon": fd_maturity_soon,
                "outflow": large_transfer or drop_high or drop_medium,
            },
            source_system="CORE_BANKING",
            triggered=fd_outflow,
        )
        if fd_outflow or include_untriggered:
            contributions.append(contribution)
        if fd_outflow:
            total += CHURN_RULE_POINTS[ChurnRuleCode.FIXED_DEPOSIT_MATURITY_WITH_OUTFLOW]

        travel_trigger = any(t.product_type == "TRAVEL_CARD" for t in triggers)
        high_forex = features is not None and features.forex_spend_30d >= HIGH_FOREX_SPEND_THRESHOLD
        forex_travel = high_forex and travel_trigger
        contribution = _contribution(
            rule_code=ChurnRuleCode.HIGH_FOREX_SPEND_WITH_TRAVEL_TRIGGER.value,
            description="High forex spend with travel-card inquiry",
            points=CHURN_RULE_POINTS[ChurnRuleCode.HIGH_FOREX_SPEND_WITH_TRAVEL_TRIGGER],
            observed_value={
                "forex_spend_30d": None if features is None else features.forex_spend_30d,
                "travel_trigger": travel_trigger,
            },
            source_system="TRANSACTION_ENGINE",
            triggered=forex_travel,
        )
        if forex_travel or include_untriggered:
            contributions.append(contribution)
        if forex_travel:
            total += CHURN_RULE_POINTS[ChurnRuleCode.HIGH_FOREX_SPEND_WITH_TRAVEL_TRIGGER]

        investment_trigger = any(
            t.product_type in {"WEALTH_MANAGEMENT", "INVESTMENT"} for t in triggers
        )
        investment_transfer = (
            external_transfer is not None
            and external_transfer >= EXTERNAL_INVESTMENT_TRANSFER_THRESHOLD
            and investment_trigger
        )
        contribution = _contribution(
            rule_code=ChurnRuleCode.EXTERNAL_INVESTMENT_TRANSFER_PATTERN.value,
            description="External investment transfer pattern detected",
            points=CHURN_RULE_POINTS[ChurnRuleCode.EXTERNAL_INVESTMENT_TRANSFER_PATTERN],
            observed_value={
                "external_transfer_amount_30d": external_transfer,
                "investment_trigger": investment_trigger,
            },
            source_system="TRANSACTION_ENGINE",
            triggered=investment_transfer,
        )
        if investment_transfer or include_untriggered:
            contributions.append(contribution)
        if investment_transfer:
            total += CHURN_RULE_POINTS[ChurnRuleCode.EXTERNAL_INVESTMENT_TRANSFER_PATTERN]

        max_dpd = credit.max_dpd_12m if credit else None
        dpd_deterioration = max_dpd is not None and max_dpd >= RECENT_DPD_DETERIORATION_THRESHOLD
        contribution = _contribution(
            rule_code=ChurnRuleCode.RECENT_DPD_DETERIORATION.value,
            description="Recent days-past-due deterioration",
            points=CHURN_RULE_POINTS[ChurnRuleCode.RECENT_DPD_DETERIORATION],
            observed_value=max_dpd,
            source_system="CREDIT_BUREAU",
            triggered=dpd_deterioration,
        )
        if dpd_deterioration or include_untriggered:
            contributions.append(contribution)
        if dpd_deterioration:
            total += CHURN_RULE_POINTS[ChurnRuleCode.RECENT_DPD_DETERIORATION]

        score = min(int(total), CHURN_SCORE_CAP)
        return ScoreResult(
            score=score,
            band=_churn_band(score),
            contributions=[c for c in contributions if c.triggered or include_untriggered],
            calculation_version=SCORING_VERSION,
            calculated_at=_utc_now(),
        )

    def calculate_customer_value(
        self,
        customer_360: Customer360Response,
        *,
        include_untriggered: bool = False,
    ) -> ScoreResult:
        """Calculate explainable customer value from Customer 360 data."""
        accounts = customer_360.accounts
        features = customer_360.transaction_features
        customer = customer_360.customer

        total_balance = sum(account.current_balance for account in accounts)
        avg_balance = sum(account.average_balance_90d for account in accounts)
        fd_balance = sum(
            account.current_balance
            for account in accounts
            if account.account_type == "FIXED_DEPOSIT"
        )
        balance_metric = total_balance + (fd_balance * 0.5) + (avg_balance * 0.25)
        balance_points = min(
            bracket_points(balance_metric, BALANCE_VALUE_BRACKETS),
            VALUE_BALANCE_MAX_POINTS,
        )

        inflow = features.monthly_inflow if features else None
        inflow_points = (
            min(bracket_points(inflow, INFLOW_VALUE_BRACKETS), VALUE_INFLOW_MAX_POINTS)
            if inflow is not None
            else 0.0
        )

        eav_points = min(
            bracket_points(customer.estimated_annual_value, EAV_VALUE_BRACKETS),
            VALUE_EAV_MAX_POINTS,
        )

        product_types = {account.account_type for account in accounts}
        depth_metric = len(accounts) + len(product_types) * 0.5
        depth_points = min(
            bracket_points(depth_metric, PRODUCT_DEPTH_BRACKETS),
            VALUE_PRODUCT_DEPTH_MAX_POINTS,
        )

        tenure_years = (date.today() - customer.relationship_start_date).days / 365.25
        tenure_points = min(
            bracket_points(tenure_years, TENURE_YEARS_BRACKETS),
            VALUE_TENURE_MAX_POINTS,
        )

        component_map = [
            (
                ValueRuleCode.BALANCE_AND_DEPOSIT_VALUE,
                balance_points,
                balance_metric,
                "CORE_BANKING",
            ),
            (ValueRuleCode.MONTHLY_INFLOW, inflow_points, inflow, "TRANSACTION_ENGINE"),
            (
                ValueRuleCode.ESTIMATED_ANNUAL_VALUE,
                eav_points,
                customer.estimated_annual_value,
                "CORE_BANKING",
            ),
            (ValueRuleCode.PRODUCT_DEPTH, depth_points, depth_metric, "CORE_BANKING"),
            (ValueRuleCode.RELATIONSHIP_TENURE, tenure_points, round(tenure_years, 2), "CRM"),
        ]

        contributions: list[RuleContribution] = []
        total = 0.0
        for code, points, observed, source in component_map:
            triggered = points > 0
            contribution = _contribution(
                rule_code=code.value,
                description=code.value.replace("_", " ").title(),
                points=points,
                observed_value=observed,
                source_system=source,
                triggered=triggered,
            )
            if triggered or include_untriggered:
                contributions.append(contribution)
            total += points

        score = min(int(round(total)), VALUE_SCORE_CAP)
        return ScoreResult(
            score=score,
            band=_value_band(score),
            contributions=contributions,
            calculation_version=SCORING_VERSION,
            calculated_at=_utc_now(),
        )

    def calculate_priority(
        self,
        *,
        churn_result: ScoreResult,
        value_result: ScoreResult,
    ) -> PriorityResult:
        """Calculate retention priority and decision band."""
        churn_weight = self.settings.churn_priority_weight
        value_weight = self.settings.value_priority_weight
        priority_score = round(
            (churn_result.score * churn_weight) + (value_result.score * value_weight)
        )
        priority_score = min(max(priority_score, 0), 100)

        if priority_score >= DECISION_RETAIN_MIN:
            decision = RecommendationDecision.RETAIN
            explanation = "High retention priority based on elevated churn risk and customer value."
        elif priority_score >= DECISION_REVIEW_MIN:
            decision = RecommendationDecision.REVIEW
            explanation = "Moderate retention priority warrants RM review."
        elif priority_score >= self.settings.decision_monitor_threshold:
            decision = RecommendationDecision.MONITOR
            explanation = "Limited retention priority; continue monitoring."
        else:
            decision = RecommendationDecision.NO_ACTION
            explanation = "Low retention priority; no immediate action required."

        return PriorityResult(
            churn_score=churn_result.score,
            value_score=value_result.score,
            churn_weight=churn_weight,
            value_weight=value_weight,
            priority_score=priority_score,
            decision=decision,
            explanation=explanation,
            calculation_version=SCORING_VERSION,
            calculated_at=_utc_now(),
        )
