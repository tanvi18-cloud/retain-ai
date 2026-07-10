"""Deterministic offer eligibility evaluation."""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.policy_rules import (
    C004_RESTRICTED_LENDING_OFFER_IDS,
    COMMUNICATION_CONSENT_WARNING,
    ELIGIBILITY_DISCLAIMER,
    LENDING_PRODUCT_TYPES,
    OFFER_CATEGORY_BY_ID,
    POLICY_VERSION,
    PRODUCT_TYPE_TO_ACCOUNT_TYPES,
    OfferCategory,
)
from app.schemas.customer_360 import Customer360Response
from app.schemas.eligibility import (
    EligibilityReason,
    EligibilityResult,
    EligibleOffer,
    RejectedOffer,
)
from app.schemas.offers import OfferDetail
from app.schemas.scoring import ScoreResult


def _utc_now() -> datetime:
    return datetime.now(UTC)


class EligibilityService:
    """Evaluate approved offers against deterministic policy rules."""

    def evaluate_offers(
        self,
        customer_360: Customer360Response,
        offers: list[OfferDetail],
        *,
        value_result: ScoreResult | None = None,
    ) -> EligibilityResult:
        """Evaluate all offers for a customer."""
        customer = customer_360.customer
        credit = customer_360.credit_profile
        held_account_types = {account.account_type for account in customer_360.accounts}
        policy_warnings: list[str] = [ELIGIBILITY_DISCLAIMER]

        if not customer.communication_consent:
            policy_warnings.append(COMMUNICATION_CONSENT_WARNING)

        eligible: list[EligibleOffer] = []
        rejected: list[RejectedOffer] = []

        for offer in offers:
            reasons: list[str] = []
            reason_codes: list[str] = []
            eligibility_reasons: list[EligibilityReason] = []

            if not offer.active:
                rejected.append(
                    RejectedOffer(
                        offer_id=offer.offer_id,
                        offer_name=offer.offer_name,
                        product_type=offer.product_type,
                        reason_codes=["INACTIVE_OFFER"],
                        explanations=["Offer is inactive and cannot be recommended."],
                    )
                )
                continue

            category = OFFER_CATEGORY_BY_ID.get(offer.offer_id, OfferCategory.NEW_LENDING)

            if (
                customer.customer_id == "C004"
                and offer.offer_id in C004_RESTRICTED_LENDING_OFFER_IDS
            ):
                reason_codes.append("C004_LENDING_RESTRICTED")
                reasons.append(
                    "Customer C004 is restricted from new home-loan and credit-card lending offers."
                )

            if customer.estimated_annual_value < offer.minimum_customer_value:
                reason_codes.append("MINIMUM_CUSTOMER_VALUE")
                reasons.append(
                    f"Estimated annual value {customer.estimated_annual_value} is below "
                    f"minimum {offer.minimum_customer_value}."
                )

            is_lending = category == OfferCategory.NEW_LENDING or (
                category == OfferCategory.UPGRADE and offer.product_type in LENDING_PRODUCT_TYPES
            )
            if is_lending:
                if credit is None:
                    reason_codes.append("MISSING_CREDIT_DATA")
                    reasons.append("Required credit data is missing for lending eligibility.")
                else:
                    if credit.default_flag:
                        reason_codes.append("DEFAULT_FLAG")
                        reasons.append("Customer default flag prevents new lending offers.")
                    if credit.max_dpd_12m > offer.maximum_dpd:
                        reason_codes.append("MAX_DPD_EXCEEDED")
                        reasons.append(
                            f"Max DPD {credit.max_dpd_12m} exceeds offer maximum "
                            f"{offer.maximum_dpd}."
                        )
                    if (
                        offer.minimum_credit_score is not None
                        and credit.credit_score < offer.minimum_credit_score
                    ):
                        reason_codes.append("MINIMUM_CREDIT_SCORE")
                        reasons.append(
                            f"Credit score {credit.credit_score} is below minimum "
                            f"{offer.minimum_credit_score}."
                        )

            if category not in {
                OfferCategory.UPGRADE,
                OfferCategory.RENEWAL,
                OfferCategory.RELATIONSHIP_REVIEW,
                OfferCategory.SUPPORT_CONSULTATION,
            }:
                mapped_types = PRODUCT_TYPE_TO_ACCOUNT_TYPES.get(
                    offer.product_type, frozenset({offer.product_type})
                )
                if mapped_types & held_account_types:
                    reason_codes.append("EXISTING_PRODUCT_HELD")
                    reasons.append(
                        f"Customer already holds {offer.product_type} and offer is not "
                        "an upgrade, renewal, relationship review, or support consultation."
                    )

            if not reason_codes:
                eligibility_reasons.append(
                    EligibilityReason(
                        code="POLICY_PASSED",
                        description="Customer meets deterministic eligibility criteria.",
                        observed_value=str(customer.customer_id),
                    )
                )
                if value_result is not None:
                    eligibility_reasons.append(
                        EligibilityReason(
                            code="VALUE_SCORE",
                            description="Customer value score evaluated for retention context.",
                            observed_value=str(value_result.score),
                        )
                    )
                eligible.append(
                    EligibleOffer(
                        offer_id=offer.offer_id,
                        offer_name=offer.offer_name,
                        product_type=offer.product_type,
                        description=offer.description,
                        estimated_cost=offer.estimated_cost,
                        expected_retention_uplift=offer.expected_retention_uplift,
                        eligibility_reasons=eligibility_reasons,
                        requires_rm_approval=offer.requires_rm_approval,
                    )
                )
            else:
                rejected.append(
                    RejectedOffer(
                        offer_id=offer.offer_id,
                        offer_name=offer.offer_name,
                        product_type=offer.product_type,
                        reason_codes=reason_codes,
                        explanations=reasons,
                    )
                )

        return EligibilityResult(
            customer_id=customer.customer_id,
            eligible_offers=eligible,
            rejected_offers=rejected,
            policy_warnings=policy_warnings,
            policy_version=POLICY_VERSION,
            evaluated_at=_utc_now(),
        )
