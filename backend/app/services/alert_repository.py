"""Alert persistence operations."""

from sqlmodel import Session, select

from app.core.exceptions import ResourceNotFoundError
from app.models.alert import Alert
from app.schemas.alerts import AlertDetail, AlertSummary
from app.schemas.common import PaginatedResponse
from app.services.repository_utils import count_query, paginate_offset, validate_pagination


def _to_summary(alert: Alert) -> AlertSummary:
    return AlertSummary(
        alert_id=alert.id,
        customer_id=alert.customer_id,
        recommendation_id=alert.recommendation_id,
        severity=alert.severity,
        title=alert.title,
        acknowledged=alert.acknowledged,
        created_at=alert.created_at,
    )


def _to_detail(alert: Alert) -> AlertDetail:
    return AlertDetail(
        alert_id=alert.id,
        customer_id=alert.customer_id,
        recommendation_id=alert.recommendation_id,
        severity=alert.severity,
        title=alert.title,
        message=alert.message,
        assigned_rm_id=alert.assigned_rm_id,
        acknowledged=alert.acknowledged,
        acknowledged_at=alert.acknowledged_at,
        created_at=alert.created_at,
    )


class AlertRepository:
    """Data access for RM alerts."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, alert_id: str) -> AlertDetail:
        """Return an alert by ID or raise when not found."""
        alert = self.session.get(Alert, alert_id)
        if alert is None:
            raise ResourceNotFoundError(
                code="ALERT_NOT_FOUND",
                message=f"Alert {alert_id} was not found",
            )
        return _to_detail(alert)

    def list_alerts(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[AlertSummary]:
        """Return paginated alerts ordered by newest first."""
        validate_pagination(page, page_size)
        statement = select(Alert).order_by(Alert.created_at.desc())
        total = count_query(self.session, statement)
        alerts = self.session.exec(
            statement.offset(paginate_offset(page, page_size)).limit(page_size)
        ).all()
        return PaginatedResponse.build(
            items=[_to_summary(alert) for alert in alerts],
            total=total,
            page=page,
            page_size=page_size,
        )

    def list_unacknowledged(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[AlertSummary]:
        """Return paginated alerts that have not been acknowledged."""
        validate_pagination(page, page_size)
        statement = (
            select(Alert)
            .where(Alert.acknowledged.is_(False))
            .order_by(Alert.created_at.desc())
        )
        total = count_query(self.session, statement)
        alerts = self.session.exec(
            statement.offset(paginate_offset(page, page_size)).limit(page_size)
        ).all()
        return PaginatedResponse.build(
            items=[_to_summary(alert) for alert in alerts],
            total=total,
            page=page,
            page_size=page_size,
        )
