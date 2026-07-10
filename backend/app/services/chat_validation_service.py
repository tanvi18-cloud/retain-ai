"""Safety validation for RM chat responses."""

from __future__ import annotations

import re
from datetime import UTC, datetime

from sqlmodel import Session

from app.core.agent_policy import AGENT_ELIGIBILITY_DISCLAIMER, PROHIBITED_APPROVAL_PHRASES
from app.core.policy_rules import C004_RESTRICTED_LENDING_OFFER_IDS
from app.schemas.chat import (
    VALID_CUSTOMER_IDS,
    ChatValidationResult,
    RMChatAgentOutput,
)
from app.tools.chat_tools import ALLOWED_CHAT_TOOLS

KNOWN_SOURCE_SYSTEMS = {
    "CORE_BANKING",
    "CREDIT_BUREAU",
    "TRANSACTION_ENGINE",
    "CRM",
}

ACCOUNT_NUMBER_PATTERN = re.compile(r"\b\d{10,}\b")
RAW_TRANSACTION_PATTERN = re.compile(
    r"\b(?:txn|transaction)\s*(?:id|ref)?\s*[:#]?\s*[A-Z0-9-]{8,}\b",
    re.IGNORECASE,
)
CHAIN_OF_THOUGHT_MARKERS = (
    "chain of thought",
    "hidden reasoning",
    "system prompt",
    "internal prompt",
)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _contains_prohibited_claim(text: str) -> list[str]:
    lowered = text.lower()
    found: list[str] = []
    for phrase in PROHIBITED_APPROVAL_PHRASES:
        if phrase in lowered and f"not {phrase}" not in lowered:
            found.append(phrase)
    return found


class ChatValidationService:
    """Validate RM chat answers before persistence."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def validate_output(
        self,
        output: RMChatAgentOutput,
        *,
        portfolio_total_revenue: float | None = None,
    ) -> ChatValidationResult:
        """Validate structured chat output."""
        errors: list[str] = []
        warnings: list[str] = []
        corrected_answer = output.answer
        corrected = False

        for customer_id in output.customer_ids:
            if customer_id not in VALID_CUSTOMER_IDS:
                errors.append(f"Unknown customer ID {customer_id}")

        for tool_name in output.used_tools:
            if tool_name not in ALLOWED_CHAT_TOOLS:
                errors.append(f"Invalid tool name: {tool_name}")

        for evidence in output.evidence:
            if evidence.source_system not in KNOWN_SOURCE_SYSTEMS:
                warnings.append(f"Unknown evidence source: {evidence.source_system}")
            if evidence.customer_id and evidence.customer_id not in VALID_CUSTOMER_IDS:
                errors.append(f"Evidence references unknown customer {evidence.customer_id}")

        if _contains_prohibited_claim(output.answer):
            errors.append("Answer contains unsupported approval or guaranteed revenue language")

        if ACCOUNT_NUMBER_PATTERN.search(output.answer):
            errors.append("Answer must not include full account numbers")

        if RAW_TRANSACTION_PATTERN.search(output.answer):
            errors.append("Answer must not include raw transaction records")

        lowered = output.answer.lower()
        if any(marker in lowered for marker in CHAIN_OF_THOUGHT_MARKERS):
            errors.append("Answer must not expose hidden prompts or chain-of-thought")

        if output.confidence < 0 or output.confidence > 1:
            errors.append("Confidence must be between 0 and 1")

        if (
            portfolio_total_revenue is not None
            and "revenue at risk" in lowered
            and f"{portfolio_total_revenue:,.0f}" not in output.answer
            and f"{portfolio_total_revenue:.2f}" not in output.answer
            and str(int(portfolio_total_revenue)) not in output.answer
        ):
            warnings.append("Portfolio revenue figure may not match deterministic totals")

        for offer_id in C004_RESTRICTED_LENDING_OFFER_IDS:
            if offer_id in output.answer and "C004" in output.customer_ids:
                errors.append("C004 lending offer must not be presented as available")

        if AGENT_ELIGIBILITY_DISCLAIMER.lower() not in lowered and any(
            word in lowered for word in ("offer", "eligible", "loan", "waiver")
        ):
            corrected_answer = f"{corrected_answer}\n\n{AGENT_ELIGIBILITY_DISCLAIMER}"
            corrected = True
            warnings.append("Eligibility disclaimer appended")

        if "guaranteed" in lowered and "not guaranteed" not in lowered:
            corrected_answer = corrected_answer.replace("guaranteed", "estimated")
            corrected = True
            warnings.append("Guaranteed language softened to estimate wording")

        return ChatValidationResult(
            valid=not errors,
            corrected=corrected and not errors,
            errors=errors,
            warnings=warnings + list(output.warnings),
            corrected_answer=corrected_answer if corrected else None,
            validated_at=_utc_now(),
        )
