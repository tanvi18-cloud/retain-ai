"""Email service tests."""

from unittest.mock import AsyncMock, patch

import pytest

from app.core.config import Settings
from app.services.email_service import EmailService


@pytest.fixture
def email_settings() -> Settings:
    return Settings(
        app_name="RetainAI",
        app_env="development",
        email_notifications_enabled=True,
        smtp_host="localhost",
        smtp_port=1025,
        smtp_from="retainai@example.local",
    )


@pytest.mark.asyncio
async def test_email_subject_and_content(email_settings: Settings):
    service = EmailService(email_settings)
    with patch("app.services.email_service.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        result = await service.send_retention_alert_email(
            to_email="rm@example.local",
            customer_id="C001",
            customer_name="Test Customer",
            primary_signal="HIGH_EXTERNAL_PRODUCT_INQUIRY",
            priority_score=80,
            revenue_at_risk=100000.0,
            recommended_action="Review retention options",
            recommended_offer="Home-loan processing-fee waiver",
        )
    assert result.success is True
    mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_disabled_email(email_settings: Settings):
    email_settings.email_notifications_enabled = False
    service = EmailService(email_settings)
    result = await service.send_retention_alert_email(
        to_email="rm@example.local",
        customer_id="C001",
        customer_name="Test Customer",
        primary_signal=None,
        priority_score=80,
        revenue_at_risk=0.0,
        recommended_action="Monitor",
        recommended_offer=None,
    )
    assert result.success is False


@pytest.mark.asyncio
async def test_smtp_failure_does_not_raise(email_settings: Settings):
    service = EmailService(email_settings)
    with patch(
        "app.services.email_service.aiosmtplib.send",
        new_callable=AsyncMock,
        side_effect=RuntimeError("smtp down"),
    ):
        result = await service.send_retention_alert_email(
            to_email="rm@example.local",
            customer_id="C001",
            customer_name="Test Customer",
            primary_signal="SIGNAL",
            priority_score=80,
            revenue_at_risk=1000.0,
            recommended_action="Act",
            recommended_offer=None,
        )
    assert result.success is False
    assert result.error is not None
