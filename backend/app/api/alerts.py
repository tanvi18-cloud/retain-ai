"""Alert management API routes."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.models.enums import AlertType, Severity
from app.schemas.alerts import AlertAcknowledgeRequest, AlertDetail, AlertSummary
from app.schemas.common import ApiErrorResponse, PaginatedResponse
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["alerts"])

NOT_FOUND_RESPONSE = {
    404: {
        "model": ApiErrorResponse,
        "description": "Alert not found",
    }
}

SortOrder = Literal["asc", "desc"]


@router.get(
    "",
    response_model=PaginatedResponse[AlertSummary],
    summary="List alerts",
)
def list_alerts(
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    customer_id: Annotated[str | None, Query()] = None,
    severity: Annotated[Severity | None, Query()] = None,
    acknowledged: Annotated[bool | None, Query()] = None,
    alert_type: Annotated[AlertType | None, Query()] = None,
    sort_order: Annotated[SortOrder, Query()] = "desc",
) -> PaginatedResponse[AlertSummary]:
    """Return paginated alerts."""
    service = AlertService(session, settings)
    return service.list_alerts(
        page=page,
        page_size=page_size,
        customer_id=customer_id,
        severity=severity,
        acknowledged=acknowledged,
        alert_type=alert_type,
        sort_order=sort_order,
    )


@router.get(
    "/{alert_id}",
    response_model=AlertDetail,
    summary="Get alert detail",
    responses=NOT_FOUND_RESPONSE,
)
def get_alert(
    alert_id: str,
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AlertDetail:
    """Return alert detail."""
    return AlertService(session, settings).get_alert(alert_id)


@router.patch(
    "/{alert_id}/acknowledge",
    response_model=AlertDetail,
    summary="Acknowledge alert",
    responses=NOT_FOUND_RESPONSE,
)
def acknowledge_alert(
    alert_id: str,
    payload: AlertAcknowledgeRequest,
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AlertDetail:
    """Acknowledge an alert idempotently."""
    service = AlertService(session, settings)
    detail = service.acknowledge_alert(alert_id, rm_id=payload.rm_id, note=payload.note)
    session.commit()
    return detail
