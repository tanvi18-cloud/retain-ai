"""SMTP email notifications for development RM alerts."""

from __future__ import annotations

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
from tenacity import retry, stop_after_attempt, wait_fixed

from app.core.config import Settings
from app.core.logging import get_logger
from app.core.policy_rules import ELIGIBILITY_DISCLAIMER
from app.schemas.notifications import EmailDeliveryResult

logger = get_logger(__name__)

EMAIL_DISCLAIMER = (
    "This alert supports RM review. Product eligibility and financial estimates are "
    "indicative and do not represent final approval or guaranteed revenue."
)


class EmailService:
    """Send safe retention alert emails via SMTP."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def smtp_configured(self) -> bool:
        return bool(self.settings.smtp_host and self.settings.smtp_from)

    async def send_retention_alert_email(
        self,
        *,
        to_email: str,
        customer_id: str,
        customer_name: str,
        primary_signal: str | None,
        priority_score: int,
        revenue_at_risk: float,
        recommended_action: str,
        recommended_offer: str | None,
    ) -> EmailDeliveryResult:
        """Send a multipart retention alert email."""
        if not self.settings.email_notifications_enabled:
            logger.info("email_notifications_disabled", customer_id=customer_id)
            return EmailDeliveryResult(success=False, error="Email notifications disabled")

        subject = f"RetainAI Alert: {customer_id} requires retention review"
        text_body = self._build_text_body(
            customer_id=customer_id,
            customer_name=customer_name,
            primary_signal=primary_signal,
            priority_score=priority_score,
            revenue_at_risk=revenue_at_risk,
            recommended_action=recommended_action,
            recommended_offer=recommended_offer,
        )
        html_body = self._build_html_body(
            customer_id=customer_id,
            customer_name=customer_name,
            primary_signal=primary_signal,
            priority_score=priority_score,
            revenue_at_risk=revenue_at_risk,
            recommended_action=recommended_action,
            recommended_offer=recommended_offer,
        )

        if self.settings.app_env == "development" and not self.smtp_configured:
            logger.info(
                "email_preview",
                customer_id=customer_id,
                subject=subject,
                to_email=to_email,
            )
            return EmailDeliveryResult(success=True, preview_logged=True)

        try:
            await self._send_message(
                to_email=to_email, subject=subject, text_body=text_body, html_body=html_body
            )
            return EmailDeliveryResult(success=True)
        except Exception as exc:
            logger.exception("email_delivery_failed", customer_id=customer_id)
            return EmailDeliveryResult(success=False, error=str(exc))

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1), reraise=True)
    async def _send_message(
        self,
        *,
        to_email: str,
        subject: str,
        text_body: str,
        html_body: str,
    ) -> None:
        message = MIMEMultipart("alternative")
        message["From"] = self.settings.smtp_from
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(text_body, "plain"))
        message.attach(MIMEText(html_body, "html"))

        await aiosmtplib.send(
            message,
            hostname=self.settings.smtp_host,
            port=self.settings.smtp_port,
            username=self.settings.smtp_username or None,
            password=self.settings.smtp_password or None,
            use_tls=self.settings.smtp_use_tls,
            timeout=self.settings.smtp_timeout_seconds,
        )

    def _build_text_body(
        self,
        *,
        customer_id: str,
        customer_name: str,
        primary_signal: str | None,
        priority_score: int,
        revenue_at_risk: float,
        recommended_action: str,
        recommended_offer: str | None,
    ) -> str:
        lines = [
            "RetainAI Retention Alert",
            "",
            f"Customer ID: {customer_id}",
            f"Customer Name: {customer_name}",
            f"Primary Signal: {primary_signal or 'Not available'}",
            f"Priority Score: {priority_score}",
            f"Revenue at Risk (estimate): {revenue_at_risk:.2f}",
            f"Recommended Action: {recommended_action}",
        ]
        if recommended_offer:
            lines.append(f"Top Eligible Discussion Offer: {recommended_offer}")
        lines.extend(["", ELIGIBILITY_DISCLAIMER, "", EMAIL_DISCLAIMER])
        return "\n".join(lines)

    def _build_html_body(
        self,
        *,
        customer_id: str,
        customer_name: str,
        primary_signal: str | None,
        priority_score: int,
        revenue_at_risk: float,
        recommended_action: str,
        recommended_offer: str | None,
    ) -> str:
        offer_row = (
            f"<li><strong>Top Eligible Discussion Offer:</strong> {recommended_offer}</li>"
            if recommended_offer
            else ""
        )
        return f"""
        <html><body>
        <h2>RetainAI Retention Alert</h2>
        <ul>
          <li><strong>Customer ID:</strong> {customer_id}</li>
          <li><strong>Customer Name:</strong> {customer_name}</li>
          <li><strong>Primary Signal:</strong> {primary_signal or 'Not available'}</li>
          <li><strong>Priority Score:</strong> {priority_score}</li>
          <li><strong>Revenue at Risk (estimate):</strong> {revenue_at_risk:.2f}</li>
          <li><strong>Recommended Action:</strong> {recommended_action}</li>
          {offer_row}
        </ul>
        <p>{ELIGIBILITY_DISCLAIMER}</p>
        <p>{EMAIL_DISCLAIMER}</p>
        </body></html>
        """
