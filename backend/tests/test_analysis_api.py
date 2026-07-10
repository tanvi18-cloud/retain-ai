"""Analysis API tests."""

from fastapi.testclient import TestClient

from app.models.enums import RecommendationDecision


def test_rules_only_analysis_c001(seeded_client: TestClient) -> None:
    response = seeded_client.post("/api/v1/analysis/C001/rules-only")
    assert response.status_code == 200
    payload = response.json()
    assert payload["customer_id"] == "C001"
    assert payload["priority_result"]["decision"] == RecommendationDecision.RETAIN.value
    assert payload["churn_result"]["score"] >= 50


def test_rules_only_missing_customer(seeded_client: TestClient) -> None:
    response = seeded_client.post("/api/v1/analysis/C999/rules-only")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CUSTOMER_NOT_FOUND"


def test_c010_rules_only_no_action(seeded_client: TestClient) -> None:
    response = seeded_client.post("/api/v1/analysis/C010/rules-only")
    assert response.status_code == 200
    payload = response.json()
    assert payload["priority_result"]["decision"] == RecommendationDecision.NO_ACTION.value
    assert payload["primary_trigger"] is None
