"""Coordinate WebSocket and email alert delivery."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Session

from app.core.config import Settings
from app.models.alert import Alert
from app.models.customer import Customer
from app.models.enums import AlertType, NotificationStatus, RecommendationDecision
from app.models.event import IncomingEvent
from app.schemas.alerts import RetentionAlertBroadcast
from app.schemas.analysis import RulesOnlyAnalysisResponse
from app.schemas.notifications import NotificationResult
from app.services.email_service import EmailService
from app.services.websocket_manager import WebSocketManager


def _utc_now() -> datetime:
    return datetime.now(UTC)


class NotificationService:
    """Deliver alerts via WebSocket and email channels."""

    def __init__(
        self,
        session: Session,
        settings: Settings,
        websocket_manager: WebSocketManager,
    ) -> None:
        self.session = session
        self.settings = settings
        self.websocket_manager = websocket_manager
        self.email_service = EmailService(settings)

    async def deliver_agent_alert(
        self,
        *,
        alert: Alert,
        event: IncomingEvent,
        customer: Customer,
    ) -> NotificationResult:
        """Deliver final agent recommendation alert notifications."""
        from app.services.recommendation_repository import RecommendationRepository

        if alert.alert_type != AlertType.AGENT_RECOMMENDATION:
            alert.notification_status = NotificationStatus.NOT_REQUIRED
            self.session.add(alert)
            return NotificationResult(
                alert_id=alert.id,
                websocket_attempted=False,
                websocket_success=False,
                websocket_connections_reached=0,
                email_attempted=False,
                email_success=False,
                final_status=NotificationStatus.NOT_REQUIRED,
                completed_at=_utc_now(),
            )

        if not event.notifications_enabled:
            alert.notification_status = NotificationStatus.NOT_REQUIRED
            self.session.add(alert)
            return NotificationResult(
                alert_id=alert.id,
                websocket_attempted=False,
                websocket_success=False,
                websocket_connections_reached=0,
                email_attempted=False,
                email_success=False,
                final_status=NotificationStatus.NOT_REQUIRED,
                completed_at=_utc_now(),
            )

        priority_score = alert.priority_score or 0
        if priority_score < self.settings.create_alert_min_priority:
            alert.notification_status = NotificationStatus.NOT_REQUIRED
            self.session.add(alert)
            return NotificationResult(
                alert_id=alert.id,
                websocket_attempted=False,
                websocket_success=False,
                websocket_connections_reached=0,
                email_attempted=False,
                email_success=False,
                final_status=NotificationStatus.NOT_REQUIRED,
                completed_at=_utc_now(),
            )

        recommended_offer = None
        expected_net_benefit = None
        decision = None
        primary_signal = alert.message
        if alert.recommendation_id:
            try:
                repo = RecommendationRepository(self.session)
                rec = repo.get_model_by_id(alert.recommendation_id)
                expected_net_benefit = rec.expected_net_benefit
                decision = rec.decision.value
            except Exception:
                rec = None
        if alert.recommended_offer_id:
            from app.services.offer_repository import OfferRepository

            try:
                recommended_offer = OfferRepository(self.session).get_by_id(
                    alert.recommended_offer_id
                ).offer_name
            except Exception:
                recommended_offer = None

        broadcast = RetentionAlertBroadcast(
            alert_type=alert.alert_type,
            alert_id=alert.id,
            event_id=event.id,
            recommendation_id=alert.recommendation_id,
            customer_id=alert.customer_id,
            severity=alert.severity,
            title=alert.title,
            priority_score=priority_score,
            recommended_action=alert.recommended_action or "Contact customer",
            recommended_offer=recommended_offer,
            expected_net_benefit=expected_net_benefit,
            created_at=alert.created_at,
        )
        websocket_attempted = True
        websocket_success = False
        websocket_connections = 0
        try:
            websocket_connections = await self.websocket_manager.broadcast_retention_alert(
                broadcast
            )
            websocket_success = websocket_connections > 0
        except Exception:
            websocket_success = False

        email_attempted = False
        email_success = False
        email_error = None
        should_email = (
            self.settings.email_notifications_enabled
            and priority_score >= self.settings.send_email_min_priority
        )
        revenue_at_risk = expected_net_benefit or 0.0
        if should_email:
            email_attempted = True
            result = await self.email_service.send_agent_alert_email(
                to_email=customer.assigned_rm_email,
                customer_id=customer.customer_id,
                customer_name=customer.full_name,
                primary_signal=primary_signal,
                priority_score=priority_score,
                decision=decision or "REVIEW",
                recommended_action=alert.recommended_action or "Review recommendation",
                recommended_offer=recommended_offer,
                revenue_at_risk=revenue_at_risk,
                expected_net_benefit=expected_net_benefit or 0.0,
            )
            email_success = result.success
            email_error = result.error

        if not websocket_attempted and not email_attempted:
            final_status = NotificationStatus.NOT_REQUIRED
        elif websocket_success and email_success:
            final_status = NotificationStatus.SENT
        elif websocket_success or email_success:
            final_status = NotificationStatus.PARTIAL
        else:
            final_status = NotificationStatus.FAILED

        alert.notification_status = final_status
        self.session.add(alert)

        return NotificationResult(
            alert_id=alert.id,
            websocket_attempted=websocket_attempted,
            websocket_success=websocket_success,
            websocket_connections_reached=websocket_connections,
            email_attempted=email_attempted,
            email_success=email_success,
            email_error=email_error,
            final_status=final_status,
            completed_at=_utc_now(),
        )

    async def deliver_alert(
        self,
        *,
        alert: Alert,
        event: IncomingEvent,
        analysis: RulesOnlyAnalysisResponse,
        customer: Customer,
    ) -> NotificationResult:
        """Broadcast and email an alert; update notification status."""
        if not event.notifications_enabled:
            alert.notification_status = NotificationStatus.NOT_REQUIRED
            self.session.add(alert)
            return NotificationResult(
                alert_id=alert.id,
                websocket_attempted=False,
                websocket_success=False,
                websocket_connections_reached=0,
                email_attempted=False,
                email_success=False,
                final_status=NotificationStatus.NOT_REQUIRED,
                completed_at=_utc_now(),
            )

        if analysis.priority_result.decision == RecommendationDecision.NO_ACTION:
            alert.notification_status = NotificationStatus.NOT_REQUIRED
            self.session.add(alert)
            return NotificationResult(
                alert_id=alert.id,
                websocket_attempted=False,
                websocket_success=False,
                websocket_connections_reached=0,
                email_attempted=False,
                email_success=False,
                final_status=NotificationStatus.NOT_REQUIRED,
                completed_at=_utc_now(),
            )

        websocket_attempted = True
        websocket_success = False
        websocket_connections = 0

        recommended_offer = None
        if analysis.financial_options:
            recommended_offer = analysis.financial_options[0].offer_name
        elif analysis.eligibility_result.eligible_offers:
            recommended_offer = analysis.eligibility_result.eligible_offers[0].offer_name

        broadcast = RetentionAlertBroadcast(
            alert_id=alert.id,
            event_id=event.id,
            customer_id=alert.customer_id,
            severity=alert.severity,
            title=alert.title,
            priority_score=alert.priority_score or analysis.priority_result.priority_score,
            recommended_action=alert.recommended_action or analysis.suggested_action,
            recommended_offer=recommended_offer,
            created_at=alert.created_at,
        )
        try:
            websocket_connections = await self.websocket_manager.broadcast_retention_alert(
                broadcast
            )
            websocket_success = websocket_connections > 0
        except Exception:
            websocket_success = False

        email_attempted = False
        email_success = False
        email_error = None
        priority_score = alert.priority_score or analysis.priority_result.priority_score

        should_email = (
            self.settings.email_notifications_enabled
            and priority_score >= self.settings.alert_priority_threshold
        )
        if should_email:
            email_attempted = True
            revenue_at_risk = 0.0
            if analysis.financial_options:
                revenue_at_risk = analysis.financial_options[0].financials.revenue_at_risk
            result = await self.email_service.send_retention_alert_email(
                to_email=customer.assigned_rm_email,
                customer_id=customer.customer_id,
                customer_name=customer.full_name,
                primary_signal=analysis.primary_trigger,
                priority_score=priority_score,
                revenue_at_risk=revenue_at_risk,
                recommended_action=alert.recommended_action or analysis.suggested_action,
                recommended_offer=recommended_offer,
            )
            email_success = result.success
            email_error = result.error

        if not websocket_attempted and not email_attempted:
            final_status = NotificationStatus.NOT_REQUIRED
        elif websocket_success and email_success:
            final_status = NotificationStatus.SENT
        elif websocket_success or email_success:
            final_status = NotificationStatus.PARTIAL
        else:
            final_status = NotificationStatus.FAILED

        alert.notification_status = final_status
        self.session.add(alert)

        return NotificationResult(
            alert_id=alert.id,
            websocket_attempted=websocket_attempted,
            websocket_success=websocket_success,
            websocket_connections_reached=websocket_connections,
            email_attempted=email_attempted,
            email_success=email_success,
            email_error=email_error,
            final_status=final_status,
            completed_at=_utc_now(),
        )
