"""Retention flow orchestration and CrewAI Flow wrapper."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from crewai.flow.flow import Flow, start
from sqlmodel import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import PolicyValidationFailedError
from app.core.logging import get_logger
from app.crews.retention_crew import RetentionCrew
from app.models.customer import Customer
from app.models.enums import (
    RecommendationDecision,
)
from app.schemas.crew_result import FlowResult
from app.schemas.flow_state import RetentionFlowState
from app.services.analysis_execution_service import AnalysisExecutionService
from app.services.analysis_service import AnalysisService
from app.services.audit_log_service import write_audit_log
from app.services.policy_validation_service import PolicyValidationService
from app.services.recommendation_service import RecommendationService

logger = get_logger(__name__)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def flow_summary(state: RetentionFlowState) -> dict[str, Any]:
    """Build a safe flow summary for event storage."""
    return {
        "execution_id": state.execution_id,
        "customer_id": state.customer_id,
        "event_id": state.event_id,
        "decision": state.priority_result.decision.value if state.priority_result else None,
        "priority_score": state.priority_result.priority_score if state.priority_result else None,
        "recommendation_id": state.recommendation_id,
        "alert_id": state.alert_id,
        "agentic_analysis_ran": state.agentic_analysis_ran,
        "validation_warnings": state.warnings,
        "current_step": state.current_step,
    }


class RetentionFlowRunner:
    """Execute the retention flow steps with database side effects."""

    def __init__(
        self,
        session: Session,
        settings: Settings | None = None,
        *,
        alert_service_factory=None,
        notification_service_factory=None,
    ) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.analysis_service = AnalysisService(session)
        self.execution_service = AnalysisExecutionService(session)
        self.recommendation_service = RecommendationService(session, self.settings)
        self.policy_validator = PolicyValidationService(session, self.settings)
        self.retention_crew = RetentionCrew(self.settings)
        self._alert_service_factory = alert_service_factory
        self._notification_service_factory = notification_service_factory

    def execute(self, state: RetentionFlowState) -> FlowResult:
        """Run the full retention flow for the given state."""
        state.started_at = state.started_at or _utc_now()
        execution = self.execution_service.get_by_id(state.execution_id)
        self.execution_service.mark_running(execution, current_step="INITIALIZE")
        write_audit_log(
            self.session,
            entity_type="analysis_executions",
            entity_id=execution.id,
            action="EXECUTION_STARTED",
            actor_type="RETENTION_FLOW",
            actor_id=execution.id,
        )

        try:
            state = self._load_customer_360(state)
            state = self._run_deterministic_analysis(state)
            write_audit_log(
                self.session,
                entity_type="analysis_executions",
                entity_id=execution.id,
                action="DETERMINISTIC_ANALYSIS_COMPLETED",
                actor_type="RETENTION_FLOW",
                details={"priority_score": state.priority_result.priority_score},
            )

            priority = state.priority_result.priority_score

            if priority < self.settings.decision_monitor_threshold:
                state = self._handle_no_action_route(state)
            elif priority < self.settings.run_full_crew_min_priority:
                state = self._handle_monitor_route(state)
            else:
                state = self._handle_full_crew_route(state)

            if state.recommendation_id:
                state = self._create_final_alert(state)
                state = self._notify_rm(state)

            execution = self.execution_service.get_by_id(state.execution_id)
            self.execution_service.mark_completed(
                execution,
                recommendation_id=state.recommendation_id,
                priority_score=priority,
                metadata=flow_summary(state),
                validation_warnings=state.warnings,
            )
            write_audit_log(
                self.session,
                entity_type="analysis_executions",
                entity_id=execution.id,
                action="EXECUTION_COMPLETED",
                actor_type="RETENTION_FLOW",
                details=flow_summary(state),
            )
            state.completed_at = _utc_now()
            return self._build_flow_result(state, status="COMPLETED")
        except Exception as exc:
            logger.exception("retention_flow_failed", execution_id=state.execution_id)
            execution = self.execution_service.get_by_id(state.execution_id)
            self.execution_service.mark_failed(
                execution,
                error_code=exc.__class__.__name__,
                safe_error_message=str(exc)[:512],
            )
            write_audit_log(
                self.session,
                entity_type="analysis_executions",
                entity_id=execution.id,
                action="EXECUTION_FAILED",
                actor_type="RETENTION_FLOW",
                details={"error": str(exc)[:512]},
            )
            state.errors.append(str(exc)[:512])
            state.completed_at = _utc_now()
            return self._build_flow_result(state, status="FAILED")

    def _load_customer_360(self, state: RetentionFlowState) -> RetentionFlowState:
        self.execution_service.update_step(
            self.execution_service.get_by_id(state.execution_id),
            "LOAD_CUSTOMER_360",
        )
        analysis = self.analysis_service.analyze_customer_rules_only(state.customer_id)
        state.rules_analysis = analysis
        state.current_step = "LOAD_CUSTOMER_360"
        return state

    def _run_deterministic_analysis(self, state: RetentionFlowState) -> RetentionFlowState:
        analysis = state.rules_analysis
        assert analysis is not None
        state.churn_result = analysis.churn_result
        state.value_result = analysis.value_result
        state.priority_result = analysis.priority_result
        state.eligibility_result = analysis.eligibility_result
        state.financial_options = analysis.financial_options
        state.current_step = "DETERMINISTIC_ANALYSIS"
        return state

    def _handle_no_action_route(self, state: RetentionFlowState) -> RetentionFlowState:
        state.current_step = "NO_ACTION_ROUTE"
        if self.recommendation_service.should_persist_no_action(
            RecommendationDecision.NO_ACTION
        ):
            rec = self.recommendation_service.create_from_rules_analysis(
                analysis=state.rules_analysis,  # type: ignore[arg-type]
                execution_id=state.execution_id,
                event_id=state.event_id,
            )
            state.recommendation_id = rec.id
        return state

    def _handle_monitor_route(self, state: RetentionFlowState) -> RetentionFlowState:
        state.current_step = "MONITOR_ROUTE"
        rec = self.recommendation_service.create_from_rules_analysis(
            analysis=state.rules_analysis,  # type: ignore[arg-type]
            execution_id=state.execution_id,
            event_id=state.event_id,
            investigation_summary=(
                "Monitor customer activity and reassess if risk signals increase."
            ),
        )
        state.recommendation_id = rec.id
        return state

    def _handle_full_crew_route(self, state: RetentionFlowState) -> RetentionFlowState:
        state.current_step = "RUN_RETENTION_CREW"
        state.agentic_analysis_ran = True
        write_audit_log(
            self.session,
            entity_type="analysis_executions",
            entity_id=state.execution_id,
            action="CREW_STARTED",
            actor_type="RETENTION_FLOW",
        )
        crew_result = self.retention_crew.kickoff(
            execution_id=state.execution_id,
            customer_id=state.customer_id,
        )
        state.crew_result = crew_result
        write_audit_log(
            self.session,
            entity_type="analysis_executions",
            entity_id=state.execution_id,
            action="CREW_COMPLETED",
            actor_type="RETENTION_FLOW",
        )

        state.current_step = "POLICY_VALIDATION"
        validation = self.policy_validator.validate_crew_result(
            customer_id=state.customer_id,
            analysis=state.rules_analysis,  # type: ignore[arg-type]
            crew_result=crew_result,
        )
        state.final_validation = validation
        state.warnings.extend(validation.warnings)
        write_audit_log(
            self.session,
            entity_type="analysis_executions",
            entity_id=state.execution_id,
            action="POLICY_VALIDATION",
            actor_type="RETENTION_FLOW",
            details={"valid": validation.valid, "errors": validation.errors},
        )
        if not validation.valid:
            raise PolicyValidationFailedError(
                message="Critical policy validation failed",
                details={"errors": validation.errors},
            )

        state.current_step = "PERSIST_RECOMMENDATION"
        rec = self.recommendation_service.create_from_crew_result(
            analysis=state.rules_analysis,  # type: ignore[arg-type]
            crew_result=crew_result,
            execution_id=state.execution_id,
            event_id=state.event_id,
            validation_warnings=state.warnings,
        )
        state.recommendation_id = rec.id
        write_audit_log(
            self.session,
            entity_type="recommendations",
            entity_id=rec.id,
            action="RECOMMENDATION_PERSISTED",
            actor_type="RETENTION_FLOW",
            details={"execution_id": state.execution_id},
        )
        return state

    def _create_final_alert(self, state: RetentionFlowState) -> RetentionFlowState:
        from app.services.alert_service import AlertService

        priority = state.priority_result.priority_score  # type: ignore[union-attr]
        decision = state.priority_result.decision  # type: ignore[union-attr]
        if priority < self.settings.create_alert_min_priority:
            return state
        if decision not in {RecommendationDecision.RETAIN, RecommendationDecision.REVIEW}:
            return state
        if state.final_validation and not state.final_validation.valid:
            return state

        alert_service = (
            self._alert_service_factory(self.session, self.settings)
            if self._alert_service_factory
            else AlertService(self.session, self.settings)
        )
        customer = self.session.get(Customer, state.customer_id)
        if customer is None or state.recommendation_id is None:
            return state

        event = None
        if state.event_id:
            from app.models.event import IncomingEvent

            event = self.session.get(IncomingEvent, state.event_id)

        alert = alert_service.create_agent_recommendation_alert(
            customer=customer,
            analysis=state.rules_analysis,  # type: ignore[arg-type]
            recommendation_id=state.recommendation_id,
            event=event,
            crew_result=state.crew_result,
        )
        if alert is not None:
            state.alert_id = alert.id
        state.current_step = "CREATE_ALERT"
        return state

    def _notify_rm(self, state: RetentionFlowState) -> RetentionFlowState:
        if not state.notifications_enabled or state.alert_id is None:
            return state
        state.current_step = "NOTIFY_RM"
        return state

    @staticmethod
    def _build_flow_result(state: RetentionFlowState, *, status: str) -> FlowResult:
        priority = state.priority_result.priority_score if state.priority_result else 0
        decision = (
            state.priority_result.decision.value
            if state.priority_result
            else RecommendationDecision.NO_ACTION.value
        )
        return FlowResult(
            execution_id=state.execution_id,
            customer_id=state.customer_id,
            event_id=state.event_id,
            decision=decision,
            priority_score=priority,
            recommendation_id=state.recommendation_id,
            alert_id=state.alert_id,
            status=status,
            agentic_analysis_ran=state.agentic_analysis_ran,
            validation_warnings=state.warnings,
            started_at=state.started_at or _utc_now(),
            completed_at=state.completed_at or _utc_now(),
            flow_summary=flow_summary(state),
        )


class RetentionFlow(Flow[RetentionFlowState]):
    """CrewAI Flow wrapper around RetentionFlowRunner."""

    def __init__(self, runner: RetentionFlowRunner, **kwargs: Any) -> None:
        self._runner = runner
        super().__init__(**kwargs)

    @start()
    def execute_retention_flow(self) -> FlowResult:
        """Entry point for CrewAI Flow execution."""
        return self._runner.execute(self.state)


def run_retention_flow(
    session: Session,
    *,
    execution_id: str,
    customer_id: str,
    event_id: str | None = None,
    notifications_enabled: bool = True,
    settings: Settings | None = None,
) -> FlowResult:
    """Run the retention flow using the orchestrator."""
    state = RetentionFlowState(
        execution_id=execution_id,
        customer_id=customer_id,
        event_id=event_id,
        notifications_enabled=notifications_enabled,
    )
    runner = RetentionFlowRunner(session, settings)
    return runner.execute(state)
