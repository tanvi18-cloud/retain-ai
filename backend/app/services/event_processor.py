"""Process queued inbound events through the retention flow."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from sqlmodel import Session

from app.core.config import Settings, get_settings
from app.core.database import get_engine
from app.core.logging import get_logger
from app.flows.retention_flow import run_retention_flow
from app.models.alert import Alert
from app.models.customer import Customer
from app.models.enums import AnalysisExecutionMode, IncomingEventStatus
from app.models.event import IncomingEvent
from app.services.analysis_execution_service import AnalysisExecutionService
from app.services.audit_log_service import write_audit_log
from app.services.event_application_service import EventApplicationService
from app.services.notification_service import NotificationService
from app.services.websocket_manager import WebSocketManager

logger = get_logger(__name__)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def analysis_snapshot(flow_summary: dict[str, Any]) -> dict[str, Any]:
    """Return a safe analysis snapshot for event storage."""
    return flow_summary


class EventProcessor:
    """Execute the full event processing workflow."""

    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.application_service = EventApplicationService(session)
        self.execution_service = AnalysisExecutionService(session)

    def process_sync(self, event_id: str) -> str | None:
        """Synchronously process a queued event; return created alert ID if any."""
        event = self.session.get(IncomingEvent, event_id)
        if event is None:
            logger.warning("event_not_found", event_id=event_id)
            return None
        if event.status == IncomingEventStatus.COMPLETED:
            return None

        event.status = IncomingEventStatus.PROCESSING
        event.processing_started_at = _utc_now()
        self.session.add(event)
        self.session.commit()

        alert_id: str | None = None
        try:
            changes = self.application_service.apply_event(event, event.payload_json)

            existing_execution = self.execution_service.find_by_event_id(event.id)
            if existing_execution and existing_execution.status.value == "COMPLETED":
                execution = existing_execution
            else:
                execution = self.execution_service.create_execution(
                    customer_id=event.customer_id,
                    mode=AnalysisExecutionMode.AGENTIC,
                    event_id=event.id,
                )

            event.execution_id = execution.id
            self.session.add(event)
            self.session.commit()

            flow_result = run_retention_flow(
                self.session,
                execution_id=execution.id,
                customer_id=event.customer_id,
                event_id=event.id,
                notifications_enabled=event.notifications_enabled,
                settings=self.settings,
            )

            snapshot = flow_result.flow_summary or {
                "execution_id": execution.id,
                "decision": flow_result.decision,
                "priority_score": flow_result.priority_score,
                "recommendation_id": flow_result.recommendation_id,
            }
            event.analysis_result_json = snapshot
            event.status = IncomingEventStatus.COMPLETED
            event.processed_at = _utc_now()
            event.error_message = None
            self.session.add(event)
            alert_id = flow_result.alert_id

            write_audit_log(
                self.session,
                entity_type="incoming_events",
                entity_id=event.id,
                action="EVENT_COMPLETED",
                actor_type="EVENT_PROCESSOR",
                actor_id=execution.id,
                details={"changes": changes, "analysis_summary": snapshot},
            )
            self.session.commit()
            return alert_id
        except Exception as exc:
            logger.exception("event_processing_failed", event_id=event_id)
            self.session.rollback()
            failed_event = self.session.get(IncomingEvent, event_id)
            if failed_event is not None:
                failed_event.status = IncomingEventStatus.FAILED
                failed_event.error_message = str(exc)[:2048]
                failed_event.retry_count += 1
                failed_event.processed_at = _utc_now()
                self.session.add(failed_event)
                write_audit_log(
                    self.session,
                    entity_type="incoming_events",
                    entity_id=event_id,
                    action="EVENT_FAILED",
                    actor_type="EVENT_PROCESSOR",
                    details={"error": failed_event.error_message},
                )
                self.session.commit()
            return None


async def deliver_notifications(
    event_id: str,
    alert_id: str | None,
    settings: Settings,
    websocket_manager: WebSocketManager,
) -> None:
    """Deliver notifications after the processing transaction has committed."""
    if alert_id is None:
        return
    with Session(get_engine()) as session:
        event = session.get(IncomingEvent, event_id)
        alert = session.get(Alert, alert_id)
        customer = session.get(Customer, event.customer_id) if event else None
        if event is None or alert is None or customer is None:
            return
        notification_service = NotificationService(session, settings, websocket_manager)
        await notification_service.deliver_agent_alert(
            alert=alert,
            event=event,
            customer=customer,
        )
        session.commit()


def create_async_processor(
    settings: Settings | None = None,
    websocket_manager: WebSocketManager | None = None,
):
    """Factory for async worker callback."""
    resolved_settings = settings or get_settings()

    async def process_event(event_id: str) -> None:
        alert_id = await asyncio.to_thread(_process_event_thread, event_id, resolved_settings)
        if websocket_manager is not None:
            await deliver_notifications(
                event_id,
                alert_id,
                resolved_settings,
                websocket_manager,
            )

    return process_event


def _process_event_thread(event_id: str, settings: Settings) -> str | None:
    with Session(get_engine()) as session:
        processor = EventProcessor(session, settings)
        return processor.process_sync(event_id)
