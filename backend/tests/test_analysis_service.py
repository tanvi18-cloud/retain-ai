"""Analysis service tests."""

import pytest
from sqlmodel import Session

from app.core.policy_rules import ELIGIBILITY_DISCLAIMER
from app.models.enums import RecommendationDecision
from app.seed.seed_database import seed_database
from app.services.analysis_service import AnalysisService


@pytest.fixture
def seeded_analysis_session(db_session: Session) -> Session:
    seed_database(db_session, skip_if_complete=False)
    return db_session


@pytest.fixture
def analysis_service(seeded_analysis_session: Session) -> AnalysisService:
    return AnalysisService(seeded_analysis_session)


def test_c001_analysis(analysis_service: AnalysisService):
    result = analysis_service.analyze_customer_rules_only("C001")
    assert result.churn_result.score >= 50
    assert result.value_result.score >= 50
    assert result.priority_result.decision == RecommendationDecision.RETAIN
    eligible_ids = {offer.offer_id for offer in result.eligibility_result.eligible_offers}
    assert "OFFER-HL-FEE" in eligible_ids or "OFFER-HL-RATE" in eligible_ids
    assert result.financial_options
    assert ELIGIBILITY_DISCLAIMER in result.eligibility_result.policy_warnings


def test_c004_restriction(analysis_service: AnalysisService):
    result = analysis_service.analyze_customer_rules_only("C004")
    rejected_ids = {offer.offer_id for offer in result.eligibility_result.rejected_offers}
    assert "OFFER-HL-FEE" in rejected_ids
    eligible_ids = {offer.offer_id for offer in result.eligibility_result.eligible_offers}
    assert "OFFER-REPAY-SUPPORT" in eligible_ids


def test_c008_fd_analysis(analysis_service: AnalysisService):
    result = analysis_service.analyze_customer_rules_only("C008")
    eligible_ids = {offer.offer_id for offer in result.eligibility_result.eligible_offers}
    assert "OFFER-FD-RENEW" in eligible_ids
    assert result.priority_result.decision in {
        RecommendationDecision.RETAIN,
        RecommendationDecision.REVIEW,
    }


def test_c010_no_action(analysis_service: AnalysisService):
    result = analysis_service.analyze_customer_rules_only("C010")
    assert result.priority_result.decision == RecommendationDecision.NO_ACTION
    assert result.primary_trigger is None


def test_missing_customer(analysis_service: AnalysisService):
    from app.core.exceptions import ResourceNotFoundError

    with pytest.raises(ResourceNotFoundError):
        analysis_service.analyze_customer_rules_only("C999")
