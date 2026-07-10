"""Alert API tests."""

import time

from fastapi.testclient import TestClient

from app.models.enums import EventType


def test_list_alerts(seeded_client: TestClient) -> None:
    response = seeded_client.get("/api/v1/alerts")
    assert response.status_code == 200


def test_acknowledge_alert(seeded_client: TestClient) -> None:
    seeded_client.post(
        "/api/v1/events",
        json={
            "customer_id": "C001",
            "event_type": EventType.MANUAL_REANALYSIS.value,
            "source_system": "CRM",
            "payload": {"reason": "alert test"},
        },
    )
    alert_id = None
    for _ in range(30):
        alerts = seeded_client.get("/api/v1/alerts", params={"customer_id": "C001"}).json()
        if alerts["items"]:
            alert_id = alerts["items"][0]["alert_id"]
            break
        time.sleep(0.1)
    if alert_id is None:
        return
    first = seeded_client.patch(
        f"/api/v1/alerts/{alert_id}/acknowledge",
        json={"rm_id": "RM001"},
    )
    second = seeded_client.patch(
        f"/api/v1/alerts/{alert_id}/acknowledge",
        json={"rm_id": "RM001"},
    )
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["acknowledged"] is True


def test_missing_alert_returns_404(seeded_client: TestClient) -> None:
    response = seeded_client.get("/api/v1/alerts/non-existent")
    assert response.status_code == 404
