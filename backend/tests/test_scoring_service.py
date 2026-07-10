"""Scoring service tests."""

from datetime import date, datetime

import pytest
from sqlmodel import Session

from app.core.scoring_rules import (
    CHURN_RULE_POINTS,
    DECISION_MONITOR_MIN,
    DECISION_RETAIN_MIN,
    DECISION_REVIEW_MIN,
    ChurnRuleCode,
)
from app.models.enums import (
    CustomerSegment,
    FreshnessStatus,
    PreferredChannel,
    RecommendationDecision,
    Severity,
)
from app.schemas.accounts import AccountDetail
from app.schemas.bureau_triggers import BureauTriggerDetail
from app.schemas.credit_profiles import CreditProfileDetail
from app.schemas.customer_360 import (
    Customer360DataFreshness,
    Customer360Response,
    DataFreshnessSource,
)
from app.schemas.customers import CustomerDetail
from app.schemas.scoring import ScoreBand
from app.schemas.transaction_features import TransactionFeatureDetail
from app.seed.seed_database import seed_database
from app.services.customer_360_service import Customer360Service
from app.services.scoring_service import ScoringService


@pytest.fixture
def seeded_scoring_session(db_session: Session) -> Session:
    seed_database(db_session, skip_if_complete=False)
    return db_session


@pytest.fixture
def scoring_service() -> ScoringService:
    return ScoringService()


def _freshness() -> Customer360DataFreshness:
    source = DataFreshnessSource(last_updated=datetime.now(), status=FreshnessStatus.FRESH)
    return Customer360DataFreshness(
        core_banking=source,
        credit_history=source,
        bureau_triggers=source,
        transaction_history=source,
    )


def _customer(**overrides) -> CustomerDetail:
    base = {
        "customer_id": "CX",
        "full_name": "Test Customer",
        "segment": CustomerSegment.STANDARD,
        "relationship_start_date": date(2015, 1, 1),
        "assigned_rm_id": "RM001",
        "assigned_rm_name": "RM",
        "assigned_rm_email": "rm@example.local",
        "communication_consent": True,
        "preferred_channel": PreferredChannel.EMAIL,
        "estimated_annual_value": 1_000_000.0,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    base.update(overrides)
    return CustomerDetail(**base)


def _features(**overrides) -> TransactionFeatureDetail:
    base = {
        "transaction_feature_id": "TF-X",
        "customer_id": "CX",
        "salary_received_current_month": True,
        "balance_change_pct_30d": 0.0,
        "monthly_inflow": 100_000.0,
        "monthly_outflow": 80_000.0,
        "external_transfer_amount_30d": 0.0,
        "card_spend_change_pct_30d": 0.0,
        "forex_spend_30d": 0.0,
        "competitor_transfer_detected": False,
        "product_inactivity_days": 0,
        "last_updated": datetime.now(),
    }
    base.update(overrides)
    return TransactionFeatureDetail(**base)


def _build_360(**kwargs) -> Customer360Response:
    defaults = {
        "customer": _customer(),
        "accounts": [],
        "credit_profile": None,
        "bureau_triggers": [],
        "transaction_features": _features(),
        "recommendations": [],
        "interactions": [],
        "data_freshness": _freshness(),
        "data_warnings": [],
    }
    defaults.update(kwargs)
    return Customer360Response(**defaults)


@pytest.mark.parametrize(
    ("rule_code", "builder"),
    [
        (
            ChurnRuleCode.HIGH_EXTERNAL_PRODUCT_INQUIRY,
            lambda: _build_360(
                bureau_triggers=[
                    BureauTriggerDetail(
                        bureau_trigger_id="T1",
                        customer_id="CX",
                        product_type="HOME_LOAN",
                        trigger_type="EXTERNAL_INQUIRY",
                        institution_category="BANK",
                        amount_band="1L",
                        severity=Severity.HIGH,
                        trigger_date=date.today(),
                        source="CREDIT_BUREAU",
                        processed=False,
                        created_at=datetime.now(),
                    )
                ]
            ),
        ),
        (
            ChurnRuleCode.SALARY_CREDIT_STOPPED,
            lambda: _build_360(transaction_features=_features(salary_received_current_month=False)),
        ),
        (
            ChurnRuleCode.BALANCE_DROP_OVER_40_PERCENT,
            lambda: _build_360(transaction_features=_features(balance_change_pct_30d=-45.0)),
        ),
        (
            ChurnRuleCode.LARGE_EXTERNAL_TRANSFER,
            lambda: _build_360(
                transaction_features=_features(external_transfer_amount_30d=600_000.0)
            ),
        ),
        (
            ChurnRuleCode.COMPETITOR_TRANSFER_DETECTED,
            lambda: _build_360(transaction_features=_features(competitor_transfer_detected=True)),
        ),
        (
            ChurnRuleCode.CARD_SPEND_DROP_OVER_30_PERCENT,
            lambda: _build_360(transaction_features=_features(card_spend_change_pct_30d=-35.0)),
        ),
        (
            ChurnRuleCode.PRODUCT_INACTIVITY_OVER_30_DAYS,
            lambda: _build_360(transaction_features=_features(product_inactivity_days=45)),
        ),
        (
            ChurnRuleCode.MULTIPLE_RECENT_CREDIT_INQUIRIES,
            lambda: _build_360(
                credit_profile=CreditProfileDetail(
                    credit_profile_id="CP",
                    customer_id="CX",
                    credit_score=700,
                    max_dpd_12m=0,
                    credit_utilization_pct=10.0,
                    active_loans=0,
                    recent_credit_inquiries=3,
                    default_flag=False,
                    last_updated=datetime.now(),
                )
            ),
        ),
        (
            ChurnRuleCode.RECENT_DPD_DETERIORATION,
            lambda: _build_360(
                credit_profile=CreditProfileDetail(
                    credit_profile_id="CP",
                    customer_id="CX",
                    credit_score=650,
                    max_dpd_12m=45,
                    credit_utilization_pct=10.0,
                    active_loans=1,
                    recent_credit_inquiries=0,
                    default_flag=False,
                    last_updated=datetime.now(),
                )
            ),
        ),
    ],
)
def test_churn_rules_trigger(scoring_service: ScoringService, rule_code: ChurnRuleCode, builder):
    result = scoring_service.calculate_churn_risk(builder())
    triggered = [c for c in result.contributions if c.rule_code == rule_code.value]
    assert triggered
    assert triggered[0].triggered
    assert triggered[0].points == CHURN_RULE_POINTS[rule_code]


def test_churn_score_capped_at_100(scoring_service: ScoringService):
    customer_360 = _build_360(
        bureau_triggers=[
            BureauTriggerDetail(
                bureau_trigger_id="T1",
                customer_id="CX",
                product_type="HOME_LOAN",
                trigger_type="EXTERNAL_INQUIRY",
                institution_category="BANK",
                amount_band="1L",
                severity=Severity.HIGH,
                trigger_date=date.today(),
                source="CREDIT_BUREAU",
                processed=False,
                created_at=datetime.now(),
            )
        ],
        transaction_features=_features(
            salary_received_current_month=False,
            balance_change_pct_30d=-50.0,
            external_transfer_amount_30d=900_000.0,
            competitor_transfer_detected=True,
            card_spend_change_pct_30d=-40.0,
            product_inactivity_days=60,
            forex_spend_30d=200_000.0,
        ),
        credit_profile=CreditProfileDetail(
            credit_profile_id="CP",
            customer_id="CX",
            credit_score=650,
            max_dpd_12m=45,
            credit_utilization_pct=10.0,
            active_loans=1,
            recent_credit_inquiries=3,
            default_flag=False,
            last_updated=datetime.now(),
        ),
        accounts=[
            AccountDetail(
                account_id="A1",
                customer_id="CX",
                account_type="FIXED_DEPOSIT",
                current_balance=1_000_000.0,
                average_balance_90d=1_000_000.0,
                salary_account=False,
                status="ACTIVE",
                fixed_deposit_maturity_date=date.today(),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ],
    )
    result = scoring_service.calculate_churn_risk(customer_360)
    assert result.score == 100


@pytest.mark.parametrize(
    ("score", "expected_band"),
    [
        (10, ScoreBand.LOW),
        (35, ScoreBand.MEDIUM),
        (55, ScoreBand.HIGH),
        (80, ScoreBand.CRITICAL),
    ],
)
def test_churn_band_mapping(scoring_service: ScoringService, score: int, expected_band: ScoreBand):
    churn = scoring_service.calculate_churn_risk(_build_360())
    value = scoring_service.calculate_customer_value(_build_360())
    priority = scoring_service.calculate_priority(churn_result=churn, value_result=value)
    assert priority.decision in RecommendationDecision


def test_value_components_present(scoring_service: ScoringService):
    customer_360 = _build_360(
        accounts=[
            AccountDetail(
                account_id="A1",
                customer_id="CX",
                account_type="SAVINGS",
                current_balance=2_000_000.0,
                average_balance_90d=1_500_000.0,
                salary_account=False,
                status="ACTIVE",
                fixed_deposit_maturity_date=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ],
        transaction_features=_features(monthly_inflow=300_000.0),
    )
    result = scoring_service.calculate_customer_value(customer_360)
    codes = {c.rule_code for c in result.contributions}
    assert "BALANCE_AND_DEPOSIT_VALUE" in codes
    assert "MONTHLY_INFLOW" in codes
    assert "ESTIMATED_ANNUAL_VALUE" in codes
    assert "PRODUCT_DEPTH" in codes
    assert "RELATIONSHIP_TENURE" in codes
    assert result.score <= 100


def test_priority_formula(scoring_service: ScoringService):
    churn = scoring_service.calculate_churn_risk(_build_360())
    value = scoring_service.calculate_customer_value(_build_360())
    priority = scoring_service.calculate_priority(churn_result=churn, value_result=value)
    expected = round((churn.score * 0.55) + (value.score * 0.45))
    assert priority.priority_score == expected


@pytest.mark.parametrize(
    ("churn", "value", "expected_decision"),
    [
        (80, 80, RecommendationDecision.RETAIN),
        (60, 60, RecommendationDecision.REVIEW),
        (40, 40, RecommendationDecision.MONITOR),
        (10, 10, RecommendationDecision.NO_ACTION),
    ],
)
def test_action_band_boundaries(
    scoring_service: ScoringService,
    churn: int,
    value: int,
    expected_decision: RecommendationDecision,
):
    from app.schemas.scoring import ScoreResult

    churn_result = ScoreResult(
        score=churn,
        band=ScoreBand.HIGH,
        contributions=[],
        calculation_version="test",
        calculated_at=datetime.now(),
    )
    value_result = ScoreResult(
        score=value,
        band=ScoreBand.HIGH,
        contributions=[],
        calculation_version="test",
        calculated_at=datetime.now(),
    )
    priority = scoring_service.calculate_priority(
        churn_result=churn_result,
        value_result=value_result,
    )
    priority_score = round((churn * 0.55) + (value * 0.45))
    if priority_score >= DECISION_RETAIN_MIN:
        assert priority.decision == RecommendationDecision.RETAIN
    elif priority_score >= DECISION_REVIEW_MIN:
        assert priority.decision == RecommendationDecision.REVIEW
    elif priority_score >= DECISION_MONITOR_MIN:
        assert priority.decision == RecommendationDecision.MONITOR
    else:
        assert priority.decision == RecommendationDecision.NO_ACTION


def test_c001_seeded_churn_and_priority(
    seeded_scoring_session: Session, scoring_service: ScoringService
):
    customer_360 = Customer360Service(seeded_scoring_session).get_customer_360("C001")
    churn = scoring_service.calculate_churn_risk(customer_360)
    value = scoring_service.calculate_customer_value(customer_360)
    priority = scoring_service.calculate_priority(churn_result=churn, value_result=value)
    assert churn.score >= 50
    assert value.score >= 50
    assert priority.decision == RecommendationDecision.RETAIN


def test_c010_seeded_no_action(seeded_scoring_session: Session, scoring_service: ScoringService):
    customer_360 = Customer360Service(seeded_scoring_session).get_customer_360("C010")
    churn = scoring_service.calculate_churn_risk(customer_360)
    priority = scoring_service.calculate_priority(
        churn_result=churn,
        value_result=scoring_service.calculate_customer_value(customer_360),
    )
    assert churn.score < 30
    assert priority.decision == RecommendationDecision.NO_ACTION
