"""WebSocket API tests."""

from fastapi.testclient import TestClient


def test_websocket_connected_message(seeded_client: TestClient) -> None:
    with seeded_client.websocket_connect("/ws/alerts") as websocket:
        message = websocket.receive_json()
        assert message["type"] == "CONNECTED"
        assert "Connected to RetainAI alerts" in message["message"]


def test_websocket_ping_pong(seeded_client: TestClient) -> None:
    with seeded_client.websocket_connect("/ws/alerts") as websocket:
        websocket.receive_json()
        websocket.send_json({"type": "PING"})
        response = websocket.receive_json()
        assert response["type"] == "PONG"
