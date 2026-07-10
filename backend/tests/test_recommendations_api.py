"""Recommendation read API tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.database import get_engine
from app.models.enums import RecommendationDecision, RecommendationStatus
from app.models.recommendation import Recommendation


def test_empty_recommendation_list(client: TestClient) -> None:
    response = client.get("/api/v1/recommendations")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 0
    assert payload["items"] == []


def test_missing_recommendation_returns_404(seeded_client: TestClient) -> None:
    response = seeded_client.get("/api/v1/recommendations/non-existent-id")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RECOMMENDATION_NOT_FOUND"


def test_recommendation_filtering(seeded_client: TestClient) -> None:
    with Session(get_engine()) as session:
        session.add(
            Recommendation(
                customer_id="C001",
                churn_score=75.0,
                value_score=80.0,
                priority_score=78.0,
                decision=RecommendationDecision.RETAIN,
                revenue_at_risk=1000.0,
                expected_net_benefit=500.0,
                confidence=0.9,
                summary="Test recommendation",
                status=RecommendationStatus.NEW,
                created_at=datetime(2026, 7, 1, tzinfo=UTC),
                updated_at=datetime(2026, 7, 1, tzinfo=UTC),
            )
        )
        session.commit()

    response = seeded_client.get(
        "/api/v1/recommendations",
        params={"customer_id": "C001", "decision": RecommendationDecision.RETAIN.value},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 1
    assert any(item["customer_id"] == "C001" for item in payload["items"])
