"""Notification service tests."""

from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel import Session

from app.core.config import Settings
from app.models.alert import Alert
from app.models.customer import Customer
from app.models.enums import AlertType, NotificationStatus, Severity
from app.models.event import IncomingEvent
from app.seed.seed_database import seed_database
from app.services.analysis_service import AnalysisService
from app.services.notification_service import NotificationService
from app.services.websocket_manager import WebSocketManager


@pytest.fixture
def seeded_notification_session(db_session: Session) -> Session:
    seed_database(db_session, skip_if_complete=False)
    return db_session


@pytest.fixture
def notification_settings() -> Settings:
    return Settings(
        app_name="RetainAI",
        app_env="development",
        email_notifications_enabled=True,
        alert_priority_threshold=70,
        smtp_host="localhost",
        smtp_from="retainai@example.local",
    )


@pytest.mark.asyncio
async def test_notification_sent(
    seeded_notification_session: Session,
    notification_settings: Settings,
):
    manager = WebSocketManager()
    ws = AsyncMock()
    ws.send_json = AsyncMock()
    await manager.connect(ws)
    analysis = AnalysisService(seeded_notification_session).analyze_customer_rules_only("C001")
    customer = seeded_notification_session.get(Customer, "C001")
    event = IncomingEvent(
        customer_id="C001",
        event_type="MANUAL_REANALYSIS",
        source_system="CRM",
        payload_json={},
        notifications_enabled=True,
    )
    alert = Alert(
        customer_id="C001",
        event_id=None,
        alert_type=AlertType.RULES_PREVIEW,
        severity=Severity.HIGH,
        title="Test",
        message="Test message",
        assigned_rm_id=customer.assigned_rm_id,
        priority_score=analysis.priority_result.priority_score,
        recommended_action=analysis.suggested_action,
        notification_status=NotificationStatus.PENDING,
    )
    seeded_notification_session.add(event)
    seeded_notification_session.add(alert)
    seeded_notification_session.commit()
    service = NotificationService(seeded_notification_session, notification_settings, manager)
    with patch(
        "app.services.email_service.aiosmtplib.send",
        new_callable=AsyncMock,
    ):
        result = await service.deliver_alert(
            alert=alert,
            event=event,
            analysis=analysis,
            customer=customer,
        )
    assert result.final_status in {NotificationStatus.SENT, NotificationStatus.PARTIAL}


@pytest.mark.asyncio
async def test_notification_not_required(
    seeded_notification_session: Session,
    notification_settings: Settings,
):
    manager = WebSocketManager()
    analysis = AnalysisService(seeded_notification_session).analyze_customer_rules_only("C010")
    customer = seeded_notification_session.get(Customer, "C010")
    event = IncomingEvent(
        customer_id="C010",
        event_type="MANUAL_REANALYSIS",
        source_system="CRM",
        payload_json={},
        notifications_enabled=False,
    )
    alert = Alert(
        customer_id="C010",
        alert_type=AlertType.RULES_PREVIEW,
        severity=Severity.LOW,
        title="Test",
        message="Test",
        assigned_rm_id=customer.assigned_rm_id,
        notification_status=NotificationStatus.PENDING,
    )
    service = NotificationService(seeded_notification_session, notification_settings, manager)
    result = await service.deliver_alert(
        alert=alert,
        event=event,
        analysis=analysis,
        customer=customer,
    )
    assert result.final_status == NotificationStatus.NOT_REQUIRED
