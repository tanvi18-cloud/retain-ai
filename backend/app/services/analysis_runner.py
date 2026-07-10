"""Background execution for manual customer analysis."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from sqlmodel import Session

from app.core.config import Settings, get_settings
from app.core.database import configure_engine, get_engine
from app.core.logging import get_logger
from app.flows.retention_flow import run_retention_flow
from app.models.alert import Alert
from app.models.customer import Customer
from app.models.event import IncomingEvent
from app.services.notification_service import NotificationService

if TYPE_CHECKING:
    from app.services.websocket_manager import WebSocketManager

logger = get_logger(__name__)

_websocket_manager: WebSocketManager | None = None


def set_websocket_manager(manager: WebSocketManager | None) -> None:
    """Register the application WebSocket manager for manual analysis notifications."""
    global _websocket_manager
    _websocket_manager = manager


def run_analysis_background(
    *,
    execution_id: str,
    customer_id: str,
    notifications_enabled: bool,
    database_url: str | None = None,
) -> None:
    """Execute the retention flow synchronously in a background worker thread."""
    settings = get_settings()
    if database_url:
        configure_engine(database_url)

    alert_id: str | None = None
    with Session(get_engine()) as session:
        try:
            flow_result = run_retention_flow(
                session,
                execution_id=execution_id,
                customer_id=customer_id,
                event_id=None,
                notifications_enabled=notifications_enabled,
                settings=settings,
            )
            alert_id = flow_result.alert_id
            session.commit()
        except Exception:
            logger.exception("manual_analysis_failed", execution_id=execution_id)
            session.rollback()
            raise

    if alert_id and notifications_enabled and _websocket_manager is not None:
        asyncio.run(
            _deliver_manual_notifications(
                execution_id=execution_id,
                alert_id=alert_id,
                customer_id=customer_id,
                settings=settings,
            )
        )


async def _deliver_manual_notifications(
    *,
    execution_id: str,
    alert_id: str,
    customer_id: str,
    settings: Settings,
) -> None:
    """Deliver notifications for manual analysis after the flow transaction commits."""
    if _websocket_manager is None:
        return

    with Session(get_engine()) as session:
        alert = session.get(Alert, alert_id)
        customer = session.get(Customer, customer_id)
        if alert is None or customer is None:
            return

        event = IncomingEvent(
            customer_id=customer_id,
            event_type="MANUAL_ANALYSIS",
            source_system="CRM",
            payload_json={"execution_id": execution_id},
            notifications_enabled=True,
        )
        session.add(event)
        session.flush()

        notification_service = NotificationService(session, settings, _websocket_manager)
        await notification_service.deliver_agent_alert(
            alert=alert,
            event=event,
            customer=customer,
        )
        session.commit()
