"""Deterministic chat intent detection for mock and real modes."""

from __future__ import annotations

import re

from app.models.enums import ChatIntent
from app.schemas.chat import VALID_CUSTOMER_IDS, IntentDetectionResult

CUSTOMER_ID_RE = re.compile(r"\bC0\d{2}\b", re.IGNORECASE)

TRIGGER_KEYWORDS: dict[str, tuple[str, ...]] = {
    "HOME_LOAN": ("home loan", "home-loan", "mortgage"),
    "CREDIT_CARD": ("credit card", "card inquiry", "card offer"),
    "SALARY_STOPPED": ("salary stopped", "salary credit stopped", "salary not received"),
    "FIXED_DEPOSIT": ("fixed deposit", "fd maturity", "fd renewal"),
    "TRAVEL": ("travel card", "travel-card", "frequent traveller"),
    "FOREX": ("forex", "foreign exchange"),
    "EXTERNAL_TRANSFER": ("external transfer", "transfer to another bank"),
    "INVESTMENT": ("investment transfer", "investment platform"),
}

UNSUPPORTED_MARKERS = (
    "delete customer",
    "approve loan",
    "send email",
    "contact customer",
    "call customer automatically",
    "sql",
    "database query",
    "hack",
    "password",
    "api key",
)


def _extract_customer_ids(message: str) -> list[str]:
    found = [match.group(0).upper() for match in CUSTOMER_ID_RE.finditer(message)]
    deduped: list[str] = []
    for customer_id in found:
        if customer_id in VALID_CUSTOMER_IDS and customer_id not in deduped:
            deduped.append(customer_id)
    return deduped


def _contains_any(message: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in message for phrase in phrases)


def _detect_trigger_type(message: str) -> str | None:
    for trigger_type, phrases in TRIGGER_KEYWORDS.items():
        if _contains_any(message, phrases):
            return trigger_type
    return None


def _extract_limit(message: str, default: int = 10) -> int:
    match = re.search(r"\b(?:top|first|show)\s+(\d{1,2})\b", message)
    if match:
        return max(1, min(int(match.group(1)), 20))
    return default


class ChatIntentService:
    """Detect supported RM chat intents deterministically."""

    def detect(self, message: str, *, has_active_customer: bool = False) -> IntentDetectionResult:
        """Return intent and extracted entities for a user message."""
        normalized = message.strip()
        lowered = normalized.lower()
        customer_ids = _extract_customer_ids(normalized)

        for marker in UNSUPPORTED_MARKERS:
            if marker in lowered:
                return IntentDetectionResult(
                    intent=ChatIntent.UNSUPPORTED,
                    confidence=0.95,
                    customer_ids=customer_ids,
                    extracted_terms=[marker],
                    unsupported_reason="Request is outside supported RM retention functionality.",
                )

        if _contains_any(
            lowered,
            ("help", "what can you do", "supported questions", "how do you work"),
        ):
            return IntentDetectionResult(
                intent=ChatIntent.GENERAL_HELP,
                confidence=0.9,
                customer_ids=customer_ids,
            )

        if _contains_any(lowered, ("compare", "versus", " vs ", "difference between")):
            if len(customer_ids) >= 2:
                return IntentDetectionResult(
                    intent=ChatIntent.CUSTOMER_COMPARISON,
                    confidence=0.95,
                    customer_ids=customer_ids[:5],
                )
            return IntentDetectionResult(
                intent=ChatIntent.UNSUPPORTED,
                confidence=0.7,
                customer_ids=customer_ids,
                unsupported_reason=(
                    "Comparison requires at least two customer IDs (e.g. C001 and C008)."
                ),
            )

        trigger_type = _detect_trigger_type(lowered)
        if trigger_type and _contains_any(
            lowered,
            ("which customers", "who has", "recent", "search", "show customers", "list customers"),
        ):
            return IntentDetectionResult(
                intent=ChatIntent.TRIGGER_SEARCH,
                confidence=0.9,
                customer_ids=customer_ids,
                trigger_type=trigger_type,
                extracted_terms=[trigger_type],
            )

        if _contains_any(
            lowered,
            ("who should i call", "call today", "priority customers", "highest priority"),
        ):
            return IntentDetectionResult(
                intent=ChatIntent.PRIORITY_CUSTOMER_LIST,
                confidence=0.92,
                customer_ids=customer_ids,
                requested_limit=_extract_limit(lowered, 10),
            )

        if _contains_any(
            lowered,
            ("high-value, high-risk", "high value high risk", "high-value high-risk"),
        ):
            return IntentDetectionResult(
                intent=ChatIntent.PRIORITY_CUSTOMER_LIST,
                confidence=0.9,
                customer_ids=customer_ids,
                requested_limit=10,
                extracted_terms=["high_value_high_risk"],
            )

        if _contains_any(
            lowered,
            ("revenue at risk", "how much revenue", "total revenue", "portfolio revenue"),
        ):
            return IntentDetectionResult(
                intent=ChatIntent.REVENUE_AT_RISK,
                confidence=0.9,
                customer_ids=customer_ids,
            )

        if _contains_any(lowered, ("portfolio summary", "portfolio overview", "portfolio status")):
            return IntentDetectionResult(
                intent=ChatIntent.PORTFOLIO_SUMMARY,
                confidence=0.88,
                customer_ids=customer_ids,
            )

        if _contains_any(lowered, ("stale data", "data freshness", "outdated data")):
            if customer_ids:
                return IntentDetectionResult(
                    intent=ChatIntent.DATA_FRESHNESS,
                    confidence=0.9,
                    customer_ids=customer_ids,
                    requires_customer_context=True,
                )
            return IntentDetectionResult(
                intent=ChatIntent.DATA_FRESHNESS,
                confidence=0.85,
                customer_ids=customer_ids,
                requested_limit=20,
            )

        if _contains_any(lowered, ("talking points", "draft talking", "what should i say")):
            target = customer_ids[0] if customer_ids else None
            return IntentDetectionResult(
                intent=ChatIntent.RM_TALKING_POINTS,
                confidence=0.9,
                customer_ids=[target] if target else [],
                requires_customer_context=target is None,
            )

        if _contains_any(
            lowered,
            ("recommendation status", "latest recommendation", "recommendation for"),
        ):
            target = customer_ids[0] if customer_ids else None
            return IntentDetectionResult(
                intent=ChatIntent.RECOMMENDATION_STATUS,
                confidence=0.9,
                customer_ids=[target] if target else [],
                requires_customer_context=target is None,
            )

        if _contains_any(lowered, ("dpd", "days past due", "past due")):
            target = customer_ids[0] if customer_ids else None
            return IntentDetectionResult(
                intent=ChatIntent.DPD_EXPLANATION,
                confidence=0.9,
                customer_ids=[target] if target else [],
                requires_customer_context=target is None,
            )

        if _contains_any(
            lowered,
            ("not eligible", "ineligible", "why can't", "why is", "blocked", "rejected offer"),
        ) and _contains_any(lowered, ("loan", "lending", "offer", "eligible", "eligibility")):
            target = customer_ids[0] if customer_ids else None
            return IntentDetectionResult(
                intent=ChatIntent.CUSTOMER_ELIGIBILITY_EXPLANATION,
                confidence=0.9,
                customer_ids=[target] if target else [],
                requires_customer_context=target is None,
            )

        if _contains_any(lowered, ("offer", "recommended offer", "what offer")):
            target = customer_ids[0] if customer_ids else None
            return IntentDetectionResult(
                intent=ChatIntent.CUSTOMER_OFFER_EXPLANATION,
                confidence=0.85,
                customer_ids=[target] if target else [],
                requires_customer_context=target is None,
            )

        if _contains_any(
            lowered,
            ("urgent", "why is", "high risk", "risk", "priority", "explain"),
        ):
            target = customer_ids[0] if customer_ids else None
            if target or has_active_customer:
                return IntentDetectionResult(
                    intent=ChatIntent.CUSTOMER_RISK_EXPLANATION,
                    confidence=0.82,
                    customer_ids=[target] if target else [],
                    requires_customer_context=target is None,
                )

        if _contains_any(
            lowered,
            ("what should i do", "what next", "next step", "follow up", "follow-up"),
        ):
            return IntentDetectionResult(
                intent=ChatIntent.FOLLOW_UP_QUESTION,
                confidence=0.8,
                customer_ids=customer_ids,
                requires_customer_context=not customer_ids and not has_active_customer,
            )

        if customer_ids and len(normalized.split()) <= 6:
            return IntentDetectionResult(
                intent=ChatIntent.FOLLOW_UP_QUESTION,
                confidence=0.65,
                customer_ids=customer_ids,
                requires_customer_context=False,
            )

        if has_active_customer and not customer_ids:
            return IntentDetectionResult(
                intent=ChatIntent.FOLLOW_UP_QUESTION,
                confidence=0.6,
                requires_customer_context=False,
            )

        return IntentDetectionResult(
            intent=ChatIntent.UNSUPPORTED,
            confidence=0.55,
            customer_ids=customer_ids,
            unsupported_reason=(
                "I can help with portfolio priorities, customer risk, eligibility, "
                "recommendations, comparisons, and talking points for customers C001–C010."
            ),
        )
