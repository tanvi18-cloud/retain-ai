"""Deterministic preview alert creation and management."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Session, select

from app.core.config import Settings
from app.models.alert import Alert
from app.models.customer import Customer
from app.models.enums import (
    AlertType,
    EventType,
    NotificationStatus,
    RecommendationDecision,
    Severity,
)
from app.models.event import IncomingEvent
from app.schemas.alerts import AlertDetail, AlertSummary
from app.schemas.analysis import RulesOnlyAnalysisResponse
from app.services.audit_log_service import write_audit_log

EVENT_ALERT_TITLES: dict[EventType, str] = {
    EventType.EXTERNAL_HOME_LOAN_INQUIRY: "External home-loan inquiry detected",
    EventType.EXTERNAL_CARD_INQUIRY: "External card inquiry detected",
    EventType.SALARY_CREDIT_STOPPED: "Salary relationship at risk",
    EventType.FIXED_DEPOSIT_MATURITY: "Fixed deposit maturity retention opportunity",
    EventType.INVESTMENT_TRANSFER_INCREASE: "External investment transfer pattern detected",
}


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _alert_severity(priority_score: int) -> Severity | None:
    if priority_score >= 85:
        return Severity.CRITICAL
    if priority_score >= 70:
        return Severity.HIGH
    if priority_score >= 50:
        return Severity.MEDIUM
    return None


class AlertService:
    """Create and manage RM alerts."""

    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    def create_preview_alert_if_needed(
        self,
        *,
        event: IncomingEvent,
        analysis: RulesOnlyAnalysisResponse,
        customer: Customer,
    ) -> Alert | None:
        """Create a deterministic rules-preview alert when thresholds are met."""
        decision = analysis.priority_result.decision
        priority_score = analysis.priority_result.priority_score
        if decision == RecommendationDecision.NO_ACTION:
            return None

        severity = _alert_severity(priority_score)
        if severity is None:
            return None

        existing = self.session.exec(
            select(Alert).where(
                Alert.event_id == event.id,
                Alert.alert_type == AlertType.RULES_PREVIEW,
            )
        ).first()
        if existing is not None:
            return existing

        try:
            event_type = EventType(event.event_type)
            title = EVENT_ALERT_TITLES.get(event_type, "Customer retention review required")
        except ValueError:
            title = "Customer retention review required"

        top_offer = None
        if analysis.financial_options:
            top_offer = analysis.financial_options[0].offer_name
        elif analysis.eligibility_result.eligible_offers:
            top_offer = analysis.eligibility_result.eligible_offers[0].offer_name

        top_offer_id = None
        if analysis.financial_options:
            top_offer_id = analysis.financial_options[0].offer_id
        elif analysis.eligibility_result.eligible_offers:
            top_offer_id = analysis.eligibility_result.eligible_offers[0].offer_id

        message = (
            f"Customer {customer.customer_id} requires retention review. "
            f"Primary signal: {analysis.primary_trigger or 'multiple signals'}. "
            f"Priority score: {priority_score}. "
            f"Suggested action: {analysis.suggested_action}."
        )

        alert = Alert(
            customer_id=customer.customer_id,
            event_id=event.id,
            recommendation_id=None,
            alert_type=AlertType.RULES_PREVIEW,
            severity=severity,
            title=title,
            message=message,
            assigned_rm_id=customer.assigned_rm_id,
            assigned_rm_email=customer.assigned_rm_email,
            priority_score=priority_score,
            recommended_action=analysis.suggested_action,
            recommended_offer_id=top_offer_id,
            notification_status=NotificationStatus.PENDING,
            acknowledged=False,
        )
        self.session.add(alert)
        self.session.flush()
        write_audit_log(
            self.session,
            entity_type="alerts",
            entity_id=alert.id,
            action="PREVIEW_ALERT_CREATED",
            actor_type="EVENT_PROCESSOR",
            actor_id=event.id,
            details={
                "customer_id": customer.customer_id,
                "priority_score": priority_score,
                "severity": severity.value,
                "recommended_offer": top_offer,
            },
        )
        return alert

    def get_alert(self, alert_id: str) -> AlertDetail:
        """Return alert detail or raise when missing."""
        alert = self.session.get(Alert, alert_id)
        if alert is None:
            from app.core.exceptions import ResourceNotFoundError

            raise ResourceNotFoundError(
                code="ALERT_NOT_FOUND",
                message=f"Alert {alert_id} was not found",
            )
        return self._to_detail(alert)

    def list_alerts(
        self,
        *,
        customer_id: str | None = None,
        severity: Severity | None = None,
        acknowledged: bool | None = None,
        alert_type: AlertType | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_order: str = "desc",
    ):
        from app.schemas.common import PaginatedResponse
        from app.services.repository_utils import count_query, paginate_offset, validate_pagination

        validate_pagination(page, page_size)
        statement = select(Alert)
        if customer_id is not None:
            statement = statement.where(Alert.customer_id == customer_id)
        if severity is not None:
            statement = statement.where(Alert.severity == severity)
        if acknowledged is not None:
            statement = statement.where(Alert.acknowledged.is_(acknowledged))
        if alert_type is not None:
            statement = statement.where(Alert.alert_type == alert_type)
        order = Alert.created_at.desc() if sort_order == "desc" else Alert.created_at.asc()
        statement = statement.order_by(order)
        total = count_query(self.session, statement)
        alerts = self.session.exec(
            statement.offset(paginate_offset(page, page_size)).limit(page_size)
        ).all()
        return PaginatedResponse.build(
            items=[self._to_summary(alert) for alert in alerts],
            total=total,
            page=page,
            page_size=page_size,
        )

    def acknowledge_alert(
        self,
        alert_id: str,
        *,
        rm_id: str,
        note: str | None = None,
    ) -> AlertDetail:
        """Acknowledge an alert idempotently."""
        alert = self.session.get(Alert, alert_id)
        if alert is None:
            from app.core.exceptions import ResourceNotFoundError

            raise ResourceNotFoundError(
                code="ALERT_NOT_FOUND",
                message=f"Alert {alert_id} was not found",
            )
        if alert.acknowledged:
            return self._to_detail(alert)

        alert.acknowledged = True
        alert.acknowledged_at = _utc_now()
        alert.acknowledged_by = rm_id
        self.session.add(alert)
        write_audit_log(
            self.session,
            entity_type="alerts",
            entity_id=alert.id,
            action="ALERT_ACKNOWLEDGED",
            actor_type="RM",
            actor_id=rm_id,
            details={"note": note},
        )
        self.session.flush()
        return self._to_detail(alert)

    @staticmethod
    def _to_summary(alert: Alert) -> AlertSummary:
        return AlertSummary(
            alert_id=alert.id,
            customer_id=alert.customer_id,
            event_id=alert.event_id,
            recommendation_id=alert.recommendation_id,
            alert_type=alert.alert_type,
            severity=alert.severity,
            title=alert.title,
            priority_score=alert.priority_score,
            acknowledged=alert.acknowledged,
            notification_status=alert.notification_status,
            created_at=alert.created_at,
        )

    @staticmethod
    def _to_detail(alert: Alert) -> AlertDetail:
        return AlertDetail(
            alert_id=alert.id,
            customer_id=alert.customer_id,
            event_id=alert.event_id,
            recommendation_id=alert.recommendation_id,
            alert_type=alert.alert_type,
            severity=alert.severity,
            title=alert.title,
            message=alert.message,
            assigned_rm_id=alert.assigned_rm_id,
            assigned_rm_email=alert.assigned_rm_email,
            priority_score=alert.priority_score,
            recommended_action=alert.recommended_action,
            recommended_offer_id=alert.recommended_offer_id,
            notification_status=alert.notification_status,
            acknowledged=alert.acknowledged,
            acknowledged_at=alert.acknowledged_at,
            acknowledged_by=alert.acknowledged_by,
            created_at=alert.created_at,
        )
