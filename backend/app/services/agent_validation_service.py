"""Post-agent policy validation for structured agent outputs."""

from __future__ import annotations

import re
from datetime import UTC, datetime

from sqlmodel import Session

from app.core.agent_policy import AGENT_ELIGIBILITY_DISCLAIMER, PROHIBITED_APPROVAL_PHRASES
from app.core.config import Settings, get_settings
from app.core.database import get_engine
from app.core.exceptions import AgentValidationFailedError
from app.core.policy_rules import C004_RESTRICTED_LENDING_OFFER_IDS
from app.models.enums import RecommendationDecision
from app.schemas.agent_outputs import (
    AgentValidationResult,
    OfferStrategyOutput,
    RetentionDecisionOutput,
    RMCopilotBrief,
    SignalInvestigation,
)
from app.schemas.analysis import RulesOnlyAnalysisResponse
from app.services.analysis_service import AnalysisService
from app.services.offer_repository import OfferRepository

FINANCIAL_TOLERANCE = 0.05


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _contains_prohibited_claim(text: str) -> list[str]:
    lowered = text.lower()
    return [phrase for phrase in PROHIBITED_APPROVAL_PHRASES if phrase in lowered]


class AgentValidationService:
    """Validate and optionally correct agent outputs against deterministic policy."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def _load_analysis(self, customer_id: str) -> RulesOnlyAnalysisResponse:
        with Session(get_engine()) as session:
            return AnalysisService(session).analyze_customer_rules_only(customer_id)

    def _eligible_offer_ids(self, analysis: RulesOnlyAnalysisResponse) -> set[str]:
        return {offer.offer_id for offer in analysis.eligibility_result.eligible_offers}

    def _validate_customer_id(self, customer_id: str, output_customer_id: str) -> list[str]:
        if output_customer_id != customer_id:
            return [f"Output customer_id {output_customer_id} does not match {customer_id}"]
        return []

    def validate_signal_investigation(
        self,
        customer_id: str,
        output: SignalInvestigation,
    ) -> AgentValidationResult:
        """Validate Signal Investigator output."""
        warnings: list[str] = []
        errors = self._validate_customer_id(customer_id, output.customer_id)
        if output.confidence < 0 or output.confidence > 1:
            errors.append("Confidence must be between 0 and 1")
        if not output.primary_signal.strip():
            errors.append("Primary signal is required")
        return AgentValidationResult(
            valid=not errors,
            corrected=False,
            warnings=warnings,
            errors=errors,
            validated_at=_utc_now(),
        )

    def validate_retention_decision(
        self,
        customer_id: str,
        output: RetentionDecisionOutput,
    ) -> AgentValidationResult:
        """Validate Retention Decision output against deterministic scores."""
        analysis = self._load_analysis(customer_id)
        warnings: list[str] = []
        errors = self._validate_customer_id(customer_id, output.customer_id)
        deterministic = analysis.priority_result.decision

        if output.deterministic_decision != deterministic:
            errors.append(
                f"Deterministic decision {output.deterministic_decision} "
                f"does not match calculated {deterministic}"
            )
        if output.agent_supported_decision != deterministic:
            warnings.append(
                "Agent supported decision differs from deterministic decision; "
                "deterministic decision is authoritative."
            )

        if output.confidence < 0 or output.confidence > 1:
            errors.append("Confidence must be between 0 and 1")

        claim_hits = _contains_prohibited_claim(output.business_reason)
        if claim_hits:
            errors.extend([f"Unsupported approval claim: {phrase}" for phrase in claim_hits])

        corrected = bool(warnings) and output.agent_supported_decision != deterministic
        return AgentValidationResult(
            valid=not errors,
            corrected=corrected,
            warnings=warnings,
            errors=errors,
            validated_at=_utc_now(),
        )

    def validate_offer_strategy(
        self,
        customer_id: str,
        output: OfferStrategyOutput,
    ) -> AgentValidationResult:
        """Validate Offer Strategy output including offer eligibility and financials."""
        analysis = self._load_analysis(customer_id)
        eligible_ids = self._eligible_offer_ids(analysis)
        warnings: list[str] = []
        errors = self._validate_customer_id(customer_id, output.customer_id)

        if output.confidence < 0 or output.confidence > 1:
            errors.append("Confidence must be between 0 and 1")

        disclaimer = output.eligibility_disclaimer.strip()
        if AGENT_ELIGIBILITY_DISCLAIMER.lower() not in disclaimer.lower():
            warnings.append("Eligibility disclaimer missing or incomplete.")
            output = output.model_copy(
                update={"eligibility_disclaimer": AGENT_ELIGIBILITY_DISCLAIMER}
            )

        for field_name, offer_id in (
            ("recommended_offer_id", output.recommended_offer_id),
            ("alternate_offer_id", output.alternate_offer_id),
        ):
            if offer_id is None:
                continue
            if offer_id not in eligible_ids:
                errors.append(f"{field_name} {offer_id} is not eligible")
            if customer_id == "C004" and offer_id in C004_RESTRICTED_LENDING_OFFER_IDS:
                errors.append(f"C004 cannot receive lending offer {offer_id}")

        with Session(get_engine()) as session:
            offers = OfferRepository(session)
            for offer_id in {output.recommended_offer_id, output.alternate_offer_id} - {None}:
                try:
                    offer = offers.get_by_id(offer_id)  # type: ignore[arg-type]
                except Exception:
                    errors.append(f"Unknown offer {offer_id}")
                    continue
                if not offer.active:
                    errors.append(f"Inactive offer {offer_id} cannot be selected")

        if output.recommended_offer_id:
            financial = next(
                (
                    option
                    for option in analysis.financial_options
                    if option.offer_id == output.recommended_offer_id
                ),
                None,
            )
            if financial and output.expected_net_benefit is not None:
                expected = financial.financials.expected_net_benefit
                if abs(output.expected_net_benefit - expected) > FINANCIAL_TOLERANCE * max(
                    abs(expected), 1
                ):
                    errors.append(
                        f"Expected net benefit {output.expected_net_benefit} "
                        f"does not match calculated {expected}"
                    )

        claim_text = " ".join(
            filter(
                None, [output.offer_rationale, output.scenario_fit, output.no_offer_reason or ""]
            )
        )
        claim_hits = _contains_prohibited_claim(claim_text)
        if claim_hits:
            errors.extend([f"Unsupported approval claim: {phrase}" for phrase in claim_hits])

        return AgentValidationResult(
            valid=not errors,
            corrected=bool(warnings) and not errors,
            warnings=warnings,
            errors=errors,
            validated_at=_utc_now(),
        )

    def validate_rm_copilot_brief(
        self,
        customer_id: str,
        output: RMCopilotBrief,
    ) -> AgentValidationResult:
        """Validate RM Copilot brief output."""
        analysis = self._load_analysis(customer_id)
        eligible_ids = self._eligible_offer_ids(analysis)
        warnings: list[str] = []
        errors = self._validate_customer_id(customer_id, output.customer_id)

        if output.confidence < 0 or output.confidence > 1:
            errors.append("Confidence must be between 0 and 1")

        if output.primary_offer_id and output.primary_offer_id not in eligible_ids:
            errors.append(f"primary_offer_id {output.primary_offer_id} is not eligible")

        combined_text = " ".join(
            [
                output.headline,
                output.executive_summary,
                output.recommended_action,
                *output.talking_points,
            ]
        )
        claim_hits = _contains_prohibited_claim(combined_text)
        if claim_hits:
            errors.extend([f"Unsupported approval claim: {phrase}" for phrase in claim_hits])

        if (
            analysis.priority_result.decision == RecommendationDecision.NO_ACTION
            and re.search(r"\b(urgent|immediate|approve)\b", combined_text, re.IGNORECASE)
        ):
            warnings.append("No-action customer brief should avoid urgent retention language.")

        if not output.prohibited_claims:
            warnings.append("Prohibited claims list is empty.")
            output = output.model_copy(
                update={"prohibited_claims": ["Do not promise product approval."]}
            )

        return AgentValidationResult(
            valid=not errors,
            corrected=bool(warnings) and not errors,
            warnings=warnings,
            errors=errors,
            validated_at=_utc_now(),
        )

    def require_valid(self, result: AgentValidationResult) -> None:
        """Raise when validation failed."""
        if not result.valid:
            raise AgentValidationFailedError(
                message="Agent output failed policy validation",
                details={"errors": result.errors, "warnings": result.warnings},
            )
