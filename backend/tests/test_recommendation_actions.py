"""Recommendation action workflow tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.database import get_engine
from app.models.audit_log import AuditLog
from app.models.enums import RecommendationDecision, RecommendationStatus
from app.models.interaction import Interaction
from app.models.recommendation import Recommendation


def _seed_recommendation(session: Session, status: RecommendationStatus = RecommendationStatus.NEW):
    rec = Recommendation(
        customer_id="C001",
        churn_score=80.0,
        value_score=70.0,
        priority_score=75.0,
        decision=RecommendationDecision.RETAIN,
        revenue_at_risk=1000.0,
        expected_net_benefit=500.0,
        confidence=0.9,
        summary="Test recommendation",
        evidence_json={"signal": "test"},
        status=status,
        created_at=datetime(2026, 7, 1, tzinfo=UTC),
        updated_at=datetime(2026, 7, 1, tzinfo=UTC),
    )
    session.add(rec)
    session.commit()
    session.refresh(rec)
    return rec


def test_valid_transition_paths(seeded_client: TestClient) -> None:
    with Session(get_engine()) as session:
        rec = _seed_recommendation(session)

    review = seeded_client.post(
        f"/api/v1/recommendations/{rec.id}/review",
        json={"rm_id": "RM001", "notes": "Reviewed"},
    )
    assert review.status_code == 200
    assert review.json()["status"] == RecommendationStatus.REVIEWED.value

    approve = seeded_client.post(
        f"/api/v1/recommendations/{rec.id}/approve",
        json={"rm_id": "RM001"},
    )
    assert approve.status_code == 200
    assert approve.json()["status"] == RecommendationStatus.APPROVED.value


def test_invalid_transition_returns_409(seeded_client: TestClient) -> None:
    with Session(get_engine()) as session:
        rec = _seed_recommendation(session, status=RecommendationStatus.CLOSED)

    response = seeded_client.post(
        f"/api/v1/recommendations/{rec.id}/approve",
        json={"rm_id": "RM001"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_STATUS_TRANSITION"


def test_rejection_requires_reason(seeded_client: TestClient) -> None:
    with Session(get_engine()) as session:
        rec = _seed_recommendation(session)

    response = seeded_client.post(
        f"/api/v1/recommendations/{rec.id}/reject",
        json={"rm_id": "RM001"},
    )
    assert response.status_code == 422


def test_repeated_idempotent_action(seeded_client: TestClient) -> None:
    with Session(get_engine()) as session:
        rec = _seed_recommendation(session)

    body = {"rm_id": "RM001", "notes": "Reviewed", "idempotency_key": "action-idem-1"}
    first = seeded_client.post(f"/api/v1/recommendations/{rec.id}/review", json=body)
    second = seeded_client.post(f"/api/v1/recommendations/{rec.id}/review", json=body)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["interaction_id"] == second.json()["interaction_id"]


def test_interaction_and_audit_created(seeded_client: TestClient) -> None:
    with Session(get_engine()) as session:
        rec = _seed_recommendation(session)

    response = seeded_client.post(
        f"/api/v1/recommendations/{rec.id}/review",
        json={"rm_id": "RM001", "notes": "Reviewed"},
    )
    assert response.status_code == 200

    with Session(get_engine()) as session:
        interactions = session.exec(
            select(Interaction).where(Interaction.recommendation_id == rec.id)
        ).all()
        audits = session.exec(
            select(AuditLog).where(AuditLog.entity_id == rec.id)
        ).all()
    assert interactions
    assert audits


def test_contacted_details_saved(seeded_client: TestClient) -> None:
    with Session(get_engine()) as session:
        rec = _seed_recommendation(session, status=RecommendationStatus.APPROVED)

    response = seeded_client.post(
        f"/api/v1/recommendations/{rec.id}/contacted",
        json={
            "rm_id": "RM001",
            "offer_presented": True,
            "contact_channel": "PHONE",
            "customer_response": "Will review offer",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == RecommendationStatus.CONTACTED.value


def test_closed_recommendation_cannot_change(seeded_client: TestClient) -> None:
    with Session(get_engine()) as session:
        rec = _seed_recommendation(session, status=RecommendationStatus.REJECTED)

    close = seeded_client.post(
        f"/api/v1/recommendations/{rec.id}/close",
        json={"rm_id": "RM001", "closing_note": "Closed after rejection"},
    )
    assert close.status_code == 200

    blocked = seeded_client.post(
        f"/api/v1/recommendations/{rec.id}/approve",
        json={"rm_id": "RM001"},
    )
    assert blocked.status_code == 409
