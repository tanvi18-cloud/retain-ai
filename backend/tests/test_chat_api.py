"""Chat API tests."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.models.enums import ChatConversationStatus


@pytest.fixture
def chat_client(seeded_client: TestClient, test_settings: Settings) -> TestClient:
    chat_settings = test_settings.model_copy(
        update={"mock_llm_mode": True, "chat_history_enabled": True}
    )
    seeded_client.app.dependency_overrides[get_settings] = lambda: chat_settings
    return seeded_client


def test_post_chat_success(chat_client: TestClient):
    response = chat_client.post(
        "/api/v1/chat",
        json={
            "message": "Why is C001 urgent?",
            "rm_id": "RM-01",
            "customer_id": "C001",
            "include_history": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["conversation_id"]
    assert payload["answer"]
    assert payload["mode"] == "MOCK"


def test_invalid_blank_message(chat_client: TestClient):
    response = chat_client.post(
        "/api/v1/chat",
        json={"message": "   ", "rm_id": "RM-01"},
    )
    assert response.status_code == 422


def test_unknown_customer(chat_client: TestClient):
    response = chat_client.post(
        "/api/v1/chat",
        json={"message": "Why urgent?", "rm_id": "RM-01", "customer_id": "C999"},
    )
    assert response.status_code == 422


def test_conversation_list(chat_client: TestClient):
    chat_client.post(
        "/api/v1/chat",
        json={"message": "Who should I call today?", "rm_id": "RM-01"},
    )
    response = chat_client.get(
        "/api/v1/chat/conversations",
        params={"rm_id": "RM-01", "page_size": 10},
    )
    assert response.status_code == 200
    assert response.json()["total"] >= 1


def test_conversation_detail(chat_client: TestClient):
    created = chat_client.post(
        "/api/v1/chat",
        json={"message": "Compare C001 and C008.", "rm_id": "RM-01"},
    ).json()
    response = chat_client.get(
        f"/api/v1/chat/conversations/{created['conversation_id']}",
        params={"rm_id": "RM-01"},
    )
    assert response.status_code == 200
    assert response.json()["conversation_id"] == created["conversation_id"]


def test_close_conversation(chat_client: TestClient):
    created = chat_client.post(
        "/api/v1/chat",
        json={"message": "Why is C001 urgent?", "rm_id": "RM-01", "customer_id": "C001"},
    ).json()
    close = chat_client.post(
        f"/api/v1/chat/conversations/{created['conversation_id']}/close",
        json={"rm_id": "RM-01"},
    )
    assert close.status_code == 200
    assert close.json()["status"] == ChatConversationStatus.CLOSED.value


def test_closed_conversation_conflict(chat_client: TestClient):
    created = chat_client.post(
        "/api/v1/chat",
        json={"message": "Why is C001 urgent?", "rm_id": "RM-01", "customer_id": "C001"},
    ).json()
    chat_client.post(
        f"/api/v1/chat/conversations/{created['conversation_id']}/close",
        json={"rm_id": "RM-01"},
    )
    response = chat_client.post(
        "/api/v1/chat",
        json={
            "message": "Follow up",
            "rm_id": "RM-01",
            "conversation_id": created["conversation_id"],
        },
    )
    assert response.status_code == 409


def test_openapi_schema(chat_client: TestClient):
    response = chat_client.get("/openapi.json")
    assert response.status_code == 200
    assert "/api/v1/chat" in response.json()["paths"]
