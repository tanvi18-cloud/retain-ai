"""System status API tests."""

from fastapi.testclient import TestClient


def test_queue_status(seeded_client: TestClient) -> None:
    response = seeded_client.get("/api/v1/system/queue-status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["worker_count"] >= 1
    assert "queue_size" in payload


def test_notification_status_safe(seeded_client: TestClient) -> None:
    response = seeded_client.get("/api/v1/system/notification-status")
    assert response.status_code == 200
    payload = response.json()
    assert "smtp_password" not in payload
    assert "email_notifications_enabled" in payload
    assert "websocket_connections" in payload
