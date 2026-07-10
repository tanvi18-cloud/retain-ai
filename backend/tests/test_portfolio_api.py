"""Portfolio API tests."""

from fastapi.testclient import TestClient

from app.models.enums import RecommendationDecision


def test_portfolio_summary(seeded_client: TestClient) -> None:
    response = seeded_client.get("/api/v1/portfolio/summary")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_customers"] == 10
    assert (
        payload["immediate_intervention_count"]
        + payload["review_count"]
        + payload["monitor_count"]
        + payload["no_action_count"]
        == 10
    )


def test_portfolio_customers_default_sort(seeded_client: TestClient) -> None:
    response = seeded_client.get("/api/v1/portfolio/customers", params={"page_size": 10})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 10
    scores = [item["priority_score"] for item in payload["items"]]
    assert scores == sorted(scores, reverse=True)


def test_portfolio_customers_filter(seeded_client: TestClient) -> None:
    response = seeded_client.get(
        "/api/v1/portfolio/customers",
        params={"decision": RecommendationDecision.NO_ACTION.value},
    )
    assert response.status_code == 200
    payload = response.json()
    assert all(
        item["decision"] == RecommendationDecision.NO_ACTION.value for item in payload["items"]
    )


def test_portfolio_customers_search(seeded_client: TestClient) -> None:
    response = seeded_client.get("/api/v1/portfolio/customers", params={"search": "C008"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
