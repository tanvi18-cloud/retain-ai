"""Central configuration for deterministic eligibility policy rules."""

from enum import StrEnum

POLICY_VERSION = "2026.07.1"

ELIGIBILITY_DISCLAIMER = (
    "Eligibility indicates an RM discussion option and does not represent final "
    "credit or product approval."
)

COMMUNICATION_CONSENT_WARNING = (
    "Communication consent is disabled; outbound marketing communication is restricted."
)


class OfferCategory(StrEnum):
    """High-level offer categories for policy checks."""

    NEW_LENDING = "NEW_LENDING"
    UPGRADE = "UPGRADE"
    RENEWAL = "RENEWAL"
    RELATIONSHIP_REVIEW = "RELATIONSHIP_REVIEW"
    SUPPORT_CONSULTATION = "SUPPORT_CONSULTATION"


LENDING_PRODUCT_TYPES: frozenset[str] = frozenset(
    {"HOME_LOAN", "PERSONAL_LOAN", "CREDIT_CARD", "TRAVEL_CARD"}
)

OFFER_CATEGORY_BY_ID: dict[str, OfferCategory] = {
    "OFFER-HL-FEE": OfferCategory.NEW_LENDING,
    "OFFER-HL-RATE": OfferCategory.NEW_LENDING,
    "OFFER-CC-FEE": OfferCategory.RENEWAL,
    "OFFER-CC-UPGRADE": OfferCategory.UPGRADE,
    "OFFER-TC-UPGRADE": OfferCategory.UPGRADE,
    "OFFER-FD-RENEW": OfferCategory.RENEWAL,
    "OFFER-PRIORITY-REVIEW": OfferCategory.RELATIONSHIP_REVIEW,
    "OFFER-REPAY-SUPPORT": OfferCategory.SUPPORT_CONSULTATION,
}

NEW_LENDING_OFFER_IDS: frozenset[str] = frozenset({"OFFER-HL-FEE", "OFFER-HL-RATE"})

CREDIT_CARD_LENDING_OFFER_IDS: frozenset[str] = frozenset({"OFFER-CC-UPGRADE"})

HOME_LOAN_LENDING_OFFER_IDS: frozenset[str] = frozenset({"OFFER-HL-FEE", "OFFER-HL-RATE"})

C004_RESTRICTED_LENDING_OFFER_IDS: frozenset[str] = frozenset(
    {
        "OFFER-HL-FEE",
        "OFFER-HL-RATE",
        "OFFER-CC-UPGRADE",
        "OFFER-CC-FEE",
        "OFFER-TC-UPGRADE",
    }
)

C004_ALLOWED_OFFER_IDS: frozenset[str] = frozenset({"OFFER-REPAY-SUPPORT", "OFFER-PRIORITY-REVIEW"})

PRODUCT_TYPE_TO_ACCOUNT_TYPES: dict[str, frozenset[str]] = {
    "HOME_LOAN": frozenset({"HOME_LOAN"}),
    "CREDIT_CARD": frozenset({"CREDIT_CARD"}),
    "TRAVEL_CARD": frozenset({"CREDIT_CARD", "TRAVEL_CARD"}),
    "FIXED_DEPOSIT": frozenset({"FIXED_DEPOSIT"}),
    "PERSONAL_LOAN": frozenset({"PERSONAL_LOAN"}),
}
