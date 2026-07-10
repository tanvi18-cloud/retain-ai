"""Analysis execution API tests."""

import time

from fastapi.testclient import TestClient

from app.models.enums import AnalysisExecutionStatus


def test_post_returns_202(seeded_client: TestClient) -> None:
    response = seeded_client.post(
        "/api/v1/analysis/C001",
        json={"notifications_enabled": False},
    )
    assert response.status_code == 202
    payload = response.json()
    assert payload["customer_id"] == "C001"
    assert payload["execution_id"]
    assert payload["status"] == AnalysisExecutionStatus.QUEUED.value
    assert "/analysis/executions/" in payload["status_url"]


def test_missing_customer_returns_404(seeded_client: TestClient) -> None:
    response = seeded_client.post("/api/v1/analysis/C999", json={})
    assert response.status_code == 404


def test_execution_can_be_polled(seeded_client: TestClient) -> None:
    create = seeded_client.post(
        "/api/v1/analysis/C001",
        json={"notifications_enabled": False},
    )
    execution_id = create.json()["execution_id"]
    for _ in range(30):
        detail = seeded_client.get(f"/api/v1/analysis/executions/{execution_id}")
        assert detail.status_code == 200
        if detail.json()["status"] in {
            AnalysisExecutionStatus.COMPLETED.value,
            AnalysisExecutionStatus.FAILED.value,
        }:
            break
        time.sleep(0.1)
    assert detail.json()["status"] in {
        AnalysisExecutionStatus.COMPLETED.value,
        AnalysisExecutionStatus.FAILED.value,
    }


def test_execution_filters(seeded_client: TestClient) -> None:
    seeded_client.post("/api/v1/analysis/C001", json={"notifications_enabled": False})
    response = seeded_client.get(
        "/api/v1/analysis/executions",
        params={"customer_id": "C001", "page_size": 5},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 1


def test_idempotent_create(seeded_client: TestClient) -> None:
    body = {"idempotency_key": "test-idem-key", "notifications_enabled": False}
    first = seeded_client.post("/api/v1/analysis/C001", json=body)
    second = seeded_client.post("/api/v1/analysis/C001", json=body)
    assert first.status_code == 202
    assert second.status_code == 202
    assert first.json()["execution_id"] == second.json()["execution_id"]


def test_completed_execution_links_recommendation(seeded_client: TestClient) -> None:
    create = seeded_client.post(
        "/api/v1/analysis/C001",
        json={"notifications_enabled": False},
    )
    execution_id = create.json()["execution_id"]
    recommendation_id = None
    for _ in range(40):
        detail = seeded_client.get(f"/api/v1/analysis/executions/{execution_id}")
        data = detail.json()
        if data["status"] == AnalysisExecutionStatus.COMPLETED.value:
            recommendation_id = data.get("recommendation_id")
            break
        time.sleep(0.1)
    assert recommendation_id is not None
