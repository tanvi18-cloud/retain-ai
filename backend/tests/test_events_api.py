"""Event API tests."""

import time

from fastapi.testclient import TestClient

from app.models.enums import EventType, IncomingEventStatus


def test_post_event_returns_202(seeded_client: TestClient) -> None:
    response = seeded_client.post(
        "/api/v1/events",
        json={
            "customer_id": "C001",
            "event_type": EventType.MANUAL_REANALYSIS.value,
            "source_system": "CRM",
            "payload": {"reason": "api test"},
        },
    )
    assert response.status_code == 202
    payload = response.json()
    assert payload["customer_id"] == "C001"
    assert payload["status"] in {
        IncomingEventStatus.QUEUED.value,
        IncomingEventStatus.COMPLETED.value,
    }


def test_invalid_payload_returns_422(seeded_client: TestClient) -> None:
    response = seeded_client.post(
        "/api/v1/events",
        json={
            "customer_id": "C001",
            "event_type": EventType.LARGE_EXTERNAL_TRANSFER.value,
            "source_system": "TRANSACTION_ENGINE",
            "payload": {"amount": -100},
        },
    )
    assert response.status_code == 422


def test_missing_customer_returns_404(seeded_client: TestClient) -> None:
    response = seeded_client.post(
        "/api/v1/events",
        json={
            "customer_id": "C999",
            "event_type": EventType.MANUAL_REANALYSIS.value,
            "source_system": "CRM",
            "payload": {},
        },
    )
    assert response.status_code == 404


def test_idempotency_returns_duplicate(seeded_client: TestClient) -> None:
    body = {
        "customer_id": "C001",
        "event_type": EventType.MANUAL_REANALYSIS.value,
        "source_system": "CRM",
        "payload": {"reason": "dup"},
        "idempotency_key": "test-key-001",
    }
    first = seeded_client.post("/api/v1/events", json=body)
    second = seeded_client.post("/api/v1/events", json=body)
    assert first.status_code == 202
    assert second.status_code == 202
    assert second.json()["duplicate"] is True
    assert first.json()["event_id"] == second.json()["event_id"]


def test_get_event_status(seeded_client: TestClient) -> None:
    created = seeded_client.post(
        "/api/v1/events",
        json={
            "customer_id": "C002",
            "event_type": EventType.EXTERNAL_CARD_INQUIRY.value,
            "source_system": "CREDIT_BUREAU",
            "payload": {"severity": "MEDIUM"},
        },
    ).json()
    for _ in range(20):
        detail = seeded_client.get(f"/api/v1/events/{created['event_id']}").json()
        if detail["status"] == IncomingEventStatus.COMPLETED.value:
            break
        time.sleep(0.1)
    assert detail["status"] == IncomingEventStatus.COMPLETED.value


def test_list_events_filter(seeded_client: TestClient) -> None:
    response = seeded_client.get(
        "/api/v1/events",
        params={"customer_id": "C001", "page_size": 10},
    )
    assert response.status_code == 200
    assert response.json()["total"] >= 0
