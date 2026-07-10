"""Final policy validation for complete crew results."""

from __future__ import annotations

import re
from datetime import UTC, datetime

from sqlmodel import Session

from app.core.agent_policy import AGENT_ELIGIBILITY_DISCLAIMER, PROHIBITED_APPROVAL_PHRASES
from app.core.config import Settings, get_settings
from app.core.policy_rules import C004_RESTRICTED_LENDING_OFFER_IDS, POLICY_VERSION
from app.models.enums import RecommendationDecision
from app.schemas.analysis import RulesOnlyAnalysisResponse
from app.schemas.crew_result import FinalPolicyValidationResult, RetentionCrewResult
from app.services.offer_repository import OfferRepository

FINANCIAL_TOLERANCE = 0.05
KNOWN_SOURCE_SYSTEMS = {
    "CORE_BANKING",
    "CREDIT_BUREAU",
    "TRANSACTION_ENGINE",
    "CRM",
}


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _contains_prohibited_claim(text: str) -> list[str]:
    lowered = text.lower()
    return [phrase for phrase in PROHIBITED_APPROVAL_PHRASES if phrase in lowered]


class PolicyValidationService:
    """Validate crew output against deterministic analysis."""

    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.offers = OfferRepository(session)

    def validate_crew_result(
        self,
        *,
        customer_id: str,
        analysis: RulesOnlyAnalysisResponse,
        crew_result: RetentionCrewResult,
    ) -> FinalPolicyValidationResult:
        """Validate a complete retention crew result."""
        errors: list[str] = []
        warnings: list[str] = []
        rejected: list[str] = []
        corrected: list[str] = []

        eligible_ids = {o.offer_id for o in analysis.eligibility_result.eligible_offers}
        priority = analysis.priority_result.priority_score
        decision = analysis.priority_result.decision

        outputs = [
            ("investigation", crew_result.investigation.customer_id),
            ("decision", crew_result.decision.customer_id),
            ("offer_strategy", crew_result.offer_strategy.customer_id),
            ("rm_brief", crew_result.rm_brief.customer_id),
        ]
        for field, output_customer in outputs:
            if output_customer != customer_id:
                errors.append(f"{field} customer_id mismatch")

        if crew_result.decision.deterministic_decision != decision:
            errors.append("Deterministic decision was altered by agent output")

        if crew_result.decision.agent_supported_decision != decision:
            warnings.append(
                "Agent supported decision differs; deterministic decision is authoritative"
            )

        offer = crew_result.offer_strategy
        if decision == RecommendationDecision.NO_ACTION and offer.recommended_offer_id:
            errors.append("NO_ACTION customers must not receive retention offers")

        if (
            customer_id == "C004"
            and offer.recommended_offer_id in C004_RESTRICTED_LENDING_OFFER_IDS
        ):
            errors.append("C004 cannot receive new lending offers")

        for field_name, offer_id in (
            ("recommended_offer_id", offer.recommended_offer_id),
            ("alternate_offer_id", offer.alternate_offer_id),
        ):
            if offer_id is None:
                continue
            if offer_id not in eligible_ids:
                errors.append(f"{field_name} {offer_id} is not eligible")
                rejected.append(field_name)
            else:
                try:
                    detail = self.offers.get_by_id(offer_id)
                    if not detail.active:
                        errors.append(f"{field_name} {offer_id} is inactive")
                        rejected.append(field_name)
                except Exception:
                    errors.append(f"Unknown offer {offer_id}")
                    rejected.append(field_name)

        if offer.recommended_offer_id:
            financial = next(
                (
                    opt
                    for opt in analysis.financial_options
                    if opt.offer_id == offer.recommended_offer_id
                ),
                None,
            )
            if financial and offer.expected_net_benefit is not None:
                expected = financial.financials.expected_net_benefit
                tolerance = FINANCIAL_TOLERANCE * max(abs(expected), 1)
                if abs(offer.expected_net_benefit - expected) > tolerance:
                    errors.append(
                        "Expected net benefit does not match deterministic calculation"
                    )

        disclaimer = offer.eligibility_disclaimer or ""
        if AGENT_ELIGIBILITY_DISCLAIMER.lower() not in disclaimer.lower():
            warnings.append("Eligibility disclaimer missing or incomplete")
            corrected.append("eligibility_disclaimer")

        combined = " ".join(
            [
                offer.offer_rationale,
                offer.scenario_fit,
                crew_result.rm_brief.executive_summary,
                *crew_result.rm_brief.talking_points,
            ]
        )
        if _contains_prohibited_claim(combined):
            errors.append("Unsupported product approval or guaranteed revenue language detected")

        if (
            decision == RecommendationDecision.MONITOR
            and priority < self.settings.run_full_crew_min_priority
            and re.search(r"\b(immediate|urgent)\b", combined, re.IGNORECASE)
            and not warnings
        ):
            warnings.append("MONITOR route should avoid urgent-contact language")

        for evidence in crew_result.investigation.evidence_references:
            if evidence.source_system not in KNOWN_SOURCE_SYSTEMS:
                warnings.append(f"Unknown evidence source system: {evidence.source_system}")

        for output in (
            crew_result.investigation.confidence,
            crew_result.decision.confidence,
            crew_result.offer_strategy.confidence,
            crew_result.rm_brief.confidence,
        ):
            if output < 0 or output > 1:
                errors.append("Confidence value out of range")

        if crew_result.validation_result and crew_result.validation_result.errors:
            errors.extend(crew_result.validation_result.errors)

        return FinalPolicyValidationResult(
            valid=not errors,
            corrected=bool(corrected) and not errors,
            errors=errors,
            warnings=warnings,
            rejected_fields=rejected,
            corrected_fields=corrected,
            validated_at=_utc_now(),
            policy_version=POLICY_VERSION,
        )
