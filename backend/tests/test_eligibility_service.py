"""Eligibility service tests."""

from datetime import datetime

import pytest
from sqlmodel import Session

from app.core.policy_rules import ELIGIBILITY_DISCLAIMER
from app.models.offer import Offer
from app.schemas.offers import OfferDetail
from app.seed.seed_database import seed_database
from app.services.customer_360_service import Customer360Service
from app.services.eligibility_service import EligibilityService


@pytest.fixture
def seeded_eligibility_session(db_session: Session) -> Session:
    seed_database(db_session, skip_if_complete=False)
    return db_session


@pytest.fixture
def eligibility_service() -> EligibilityService:
    return EligibilityService()


def _inactive_offer() -> OfferDetail:
    return OfferDetail(
        offer_id="OFFER-INACTIVE",
        product_type="LOAN",
        offer_name="Inactive",
        description="Inactive offer",
        minimum_credit_score=650,
        maximum_dpd=30,
        minimum_customer_value=0.0,
        maximum_offer_cost=1000.0,
        estimated_cost=500.0,
        expected_retention_uplift=0.1,
        active=False,
        requires_rm_approval=False,
        created_at=datetime.now(),
    )


def test_inactive_offer_blocked(
    eligibility_service: EligibilityService, seeded_eligibility_session: Session
):
    customer_360 = Customer360Service(seeded_eligibility_session).get_customer_360("C001")
    result = eligibility_service.evaluate_offers(customer_360, [_inactive_offer()])
    assert result.rejected_offers
    assert result.rejected_offers[0].reason_codes == ["INACTIVE_OFFER"]


def test_c001_home_loan_eligible(
    eligibility_service: EligibilityService, seeded_eligibility_session: Session
):
    customer_360 = Customer360Service(seeded_eligibility_session).get_customer_360("C001")
    offers = [_offer_detail(offer_id) for offer_id in ["OFFER-HL-FEE", "OFFER-HL-RATE"]]
    result = eligibility_service.evaluate_offers(customer_360, offers)
    eligible_ids = {offer.offer_id for offer in result.eligible_offers}
    assert "OFFER-HL-FEE" in eligible_ids or "OFFER-HL-RATE" in eligible_ids


def test_c004_lending_rejected(
    eligibility_service: EligibilityService, seeded_eligibility_session: Session
):
    customer_360 = Customer360Service(seeded_eligibility_session).get_customer_360("C004")
    offers = [
        _seed_offer_detail(seeded_eligibility_session, offer_id)
        for offer_id in [
            "OFFER-HL-FEE",
            "OFFER-CC-UPGRADE",
            "OFFER-REPAY-SUPPORT",
        ]
    ]
    result = eligibility_service.evaluate_offers(customer_360, offers)
    rejected_ids = {offer.offer_id for offer in result.rejected_offers}
    assert "OFFER-HL-FEE" in rejected_ids
    assert "OFFER-CC-UPGRADE" in rejected_ids
    eligible_ids = {offer.offer_id for offer in result.eligible_offers}
    assert "OFFER-REPAY-SUPPORT" in eligible_ids
    assert ELIGIBILITY_DISCLAIMER in result.policy_warnings


def test_c007_travel_card_eligible(
    eligibility_service: EligibilityService, seeded_eligibility_session: Session
):
    customer_360 = Customer360Service(seeded_eligibility_session).get_customer_360("C007")
    offer = _seed_offer_detail(seeded_eligibility_session, "OFFER-TC-UPGRADE")
    result = eligibility_service.evaluate_offers(customer_360, [offer])
    assert any(item.offer_id == "OFFER-TC-UPGRADE" for item in result.eligible_offers)


def test_c008_fd_renewal_eligible(
    eligibility_service: EligibilityService, seeded_eligibility_session: Session
):
    customer_360 = Customer360Service(seeded_eligibility_session).get_customer_360("C008")
    offer = _seed_offer_detail(seeded_eligibility_session, "OFFER-FD-RENEW")
    result = eligibility_service.evaluate_offers(customer_360, [offer])
    assert any(item.offer_id == "OFFER-FD-RENEW" for item in result.eligible_offers)


def test_communication_consent_warning(
    seeded_eligibility_session: Session, eligibility_service: EligibilityService
):
    customer_360 = Customer360Service(seeded_eligibility_session).get_customer_360("C001")
    customer_360.customer.communication_consent = False
    offer = _seed_offer_detail(seeded_eligibility_session, "OFFER-PRIORITY-REVIEW")
    result = eligibility_service.evaluate_offers(customer_360, [offer])
    assert any("communication" in warning.lower() for warning in result.policy_warnings)


def test_minimum_customer_value_rule(
    eligibility_service: EligibilityService, seeded_eligibility_session: Session
):
    customer_360 = Customer360Service(seeded_eligibility_session).get_customer_360("C006")
    offer = _seed_offer_detail(seeded_eligibility_session, "OFFER-HL-FEE")
    result = eligibility_service.evaluate_offers(customer_360, [offer])
    rejected = next(item for item in result.rejected_offers if item.offer_id == "OFFER-HL-FEE")
    assert "MINIMUM_CUSTOMER_VALUE" in rejected.reason_codes


def test_dpd_rule(eligibility_service: EligibilityService, seeded_eligibility_session: Session):
    customer_360 = Customer360Service(seeded_eligibility_session).get_customer_360("C004")
    offer = OfferDetail(
        offer_id="OFFER-TEST-DPD",
        product_type="RELATIONSHIP",
        offer_name="Test review",
        description="Test",
        minimum_credit_score=500,
        maximum_dpd=30,
        minimum_customer_value=0.0,
        maximum_offer_cost=1000.0,
        estimated_cost=500.0,
        expected_retention_uplift=0.1,
        active=True,
        requires_rm_approval=False,
        created_at=datetime.now(),
    )
    result = eligibility_service.evaluate_offers(customer_360, [offer])
    rejected = result.rejected_offers[0]
    assert "MAX_DPD_EXCEEDED" in rejected.reason_codes


def test_existing_product_restriction(
    eligibility_service: EligibilityService, seeded_eligibility_session: Session
):
    customer_360 = Customer360Service(seeded_eligibility_session).get_customer_360("C002")
    offer = OfferDetail(
        offer_id="OFFER-TEST-CC-NEW",
        product_type="CREDIT_CARD",
        offer_name="New card",
        description="New card lending",
        minimum_credit_score=700,
        maximum_dpd=15,
        minimum_customer_value=0.0,
        maximum_offer_cost=1000.0,
        estimated_cost=500.0,
        expected_retention_uplift=0.1,
        active=True,
        requires_rm_approval=False,
        created_at=datetime.now(),
    )
    result = eligibility_service.evaluate_offers(customer_360, [offer])
    rejected = result.rejected_offers[0]
    assert "EXISTING_PRODUCT_HELD" in rejected.reason_codes


def _seed_offer_detail(session: Session, offer_id: str) -> OfferDetail:
    offer = session.get(Offer, offer_id)
    assert offer is not None
    return OfferDetail.model_validate(offer)


def _offer_detail(offer_id: str) -> OfferDetail:
    return OfferDetail(
        offer_id=offer_id,
        product_type="HOME_LOAN",
        offer_name="Test",
        description="Test",
        minimum_credit_score=700,
        maximum_dpd=30,
        minimum_customer_value=500_000.0,
        maximum_offer_cost=50_000.0,
        estimated_cost=10_000.0,
        expected_retention_uplift=0.2,
        active=True,
        requires_rm_approval=True,
        created_at=datetime.now(),
    )
