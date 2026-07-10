"""Sequential four-agent retention crew."""

from __future__ import annotations

import time
from datetime import UTC, datetime

import crewai

from app.agents.offer_strategy_agent import run_offer_strategy
from app.agents.retention_decision_agent import run_retention_decision
from app.agents.rm_copilot_agent import run_rm_copilot
from app.agents.signal_investigator import run_signal_investigator
from app.core.agent_policy import AGENT_ELIGIBILITY_DISCLAIMER
from app.core.config import Settings, get_settings
from app.core.exceptions import AgentExecutionError
from app.core.policy_rules import POLICY_VERSION
from app.core.scoring_rules import SCORING_VERSION
from app.schemas.agent_outputs import AgentValidationResult
from app.schemas.crew_result import CrewExecutionMetadata, RetentionCrewResult
from app.schemas.llm import LLMMode
from app.services.agent_validation_service import AgentValidationService


def _utc_now() -> datetime:
    return datetime.now(UTC)


class RetentionCrew:
    """Run the four-agent retention pipeline in strict sequence."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.validator = AgentValidationService(self.settings)

    def kickoff(self, *, execution_id: str, customer_id: str) -> RetentionCrewResult:
        """Execute investigation → decision → offer strategy → RM brief."""
        started = _utc_now()
        start_ms = time.perf_counter()
        task_durations: dict[str, int] = {}
        warnings: list[str] = []

        try:
            t0 = time.perf_counter()
            investigation = run_signal_investigator(customer_id, settings=self.settings)
            task_durations["signal_investigation"] = int((time.perf_counter() - t0) * 1000)

            t0 = time.perf_counter()
            decision = run_retention_decision(
                customer_id,
                investigation,
                settings=self.settings,
            )
            task_durations["retention_decision"] = int((time.perf_counter() - t0) * 1000)

            t0 = time.perf_counter()
            offer_strategy = run_offer_strategy(
                customer_id,
                investigation,
                decision,
                settings=self.settings,
            )
            task_durations["offer_strategy"] = int((time.perf_counter() - t0) * 1000)

            t0 = time.perf_counter()
            rm_brief = run_rm_copilot(
                customer_id,
                investigation,
                decision,
                offer_strategy,
                settings=self.settings,
            )
            task_durations["rm_brief"] = int((time.perf_counter() - t0) * 1000)
        except Exception as exc:
            raise AgentExecutionError(
                message="Retention crew execution failed",
                details={"customer_id": customer_id, "error_type": exc.__class__.__name__},
            ) from exc

        validation = self._aggregate_validation(
            customer_id, investigation, decision, offer_strategy, rm_brief
        )
        if validation.warnings:
            warnings.extend(validation.warnings)

        completed = _utc_now()
        mode = LLMMode.MOCK if self.settings.mock_llm_mode else LLMMode.QWEN
        metadata = CrewExecutionMetadata(
            mode=mode,
            configured_model=self.settings.qwen_model,
            duration_ms=int((time.perf_counter() - start_ms) * 1000),
            calculation_version=SCORING_VERSION,
            eligibility_policy_version=POLICY_VERSION,
            agent_policy_version=POLICY_VERSION,
            crewai_version=getattr(crewai, "__version__", None),
            task_durations_ms=task_durations,
        )

        return RetentionCrewResult(
            execution_id=execution_id,
            customer_id=customer_id,
            investigation=investigation,
            decision=decision,
            offer_strategy=offer_strategy,
            rm_brief=rm_brief,
            validation_result=validation,
            execution_metadata=metadata,
            validation_warnings=warnings,
            started_at=started,
            completed_at=completed,
        )

    def _aggregate_validation(
        self,
        customer_id: str,
        investigation,
        decision,
        offer_strategy,
        rm_brief,
    ) -> AgentValidationResult:
        results = [
            self.validator.validate_signal_investigation(customer_id, investigation),
            self.validator.validate_retention_decision(customer_id, decision),
            self.validator.validate_offer_strategy(customer_id, offer_strategy),
            self.validator.validate_rm_copilot_brief(customer_id, rm_brief),
        ]
        errors: list[str] = []
        warnings: list[str] = []
        for result in results:
            errors.extend(result.errors)
            warnings.extend(result.warnings)
        if not offer_strategy.eligibility_disclaimer:
            offer_strategy = offer_strategy.model_copy(
                update={"eligibility_disclaimer": AGENT_ELIGIBILITY_DISCLAIMER}
            )
        return AgentValidationResult(
            valid=not errors,
            corrected=any(r.corrected for r in results),
            warnings=warnings,
            errors=errors,
            validated_at=_utc_now(),
        )
