"""WebSocket manager tests."""

import pytest

from app.services.websocket_manager import WebSocketManager


class FakeWebSocket:
    def __init__(self) -> None:
        self.accepted = False
        self.sent: list[dict] = []
        self.closed = False

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, payload: dict) -> None:
        if payload.get("fail"):
            raise RuntimeError("send failed")
        self.sent.append(payload)

    async def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_connect_and_disconnect():
    manager = WebSocketManager()
    ws = FakeWebSocket()
    connection_id = await manager.connect(ws)
    assert ws.accepted
    assert manager.connection_count == 1
    await manager.disconnect(connection_id)
    assert manager.connection_count == 0


@pytest.mark.asyncio
async def test_broadcast_reaches_clients():
    manager = WebSocketManager()
    ws1 = FakeWebSocket()
    ws2 = FakeWebSocket()
    await manager.connect(ws1)
    await manager.connect(ws2)
    delivered = await manager.broadcast({"type": "TEST"})
    assert delivered == 2


@pytest.mark.asyncio
async def test_failed_client_removed():
    manager = WebSocketManager()
    ws = FakeWebSocket()
    connection_id = await manager.connect(ws)
    delivered = await manager.send_json(connection_id, {"fail": True})
    assert delivered is False
    assert manager.connection_count == 0
