"""WebSocket connection manager for live RM alerts."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import WebSocket

from app.core.logging import get_logger
from app.schemas.alerts import RetentionAlertBroadcast

logger = get_logger(__name__)


class WebSocketManager:
    """Track active WebSocket connections and broadcast alert payloads."""

    def __init__(self) -> None:
        self._connections: dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()

    @property
    def connection_count(self) -> int:
        return len(self._connections)

    async def connect(self, websocket: WebSocket) -> str:
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        connection_id = str(uuid4())
        async with self._lock:
            self._connections[connection_id] = websocket
        logger.info("websocket_connected", connection_count=self.connection_count)
        return connection_id

    async def disconnect(self, connection_id: str) -> None:
        """Remove a WebSocket connection from the registry."""
        async with self._lock:
            self._connections.pop(connection_id, None)
        logger.info("websocket_disconnected", connection_count=self.connection_count)

    async def send_json(self, connection_id: str, payload: dict[str, Any]) -> bool:
        """Send JSON to a single connection; remove on failure."""
        async with self._lock:
            websocket = self._connections.get(connection_id)
        if websocket is None:
            return False
        try:
            await websocket.send_json(payload)
            return True
        except Exception:
            logger.warning("websocket_send_failed", connection_id=connection_id)
            await self.disconnect(connection_id)
            return False

    async def broadcast(self, payload: dict[str, Any]) -> int:
        """Broadcast JSON to all connections; failed sends are cleaned up."""
        async with self._lock:
            items = list(self._connections.items())
        delivered = 0
        for connection_id, websocket in items:
            try:
                await websocket.send_json(payload)
                delivered += 1
            except Exception:
                logger.warning("websocket_broadcast_failed", connection_id=connection_id)
                await self.disconnect(connection_id)
        return delivered

    async def broadcast_retention_alert(self, alert: RetentionAlertBroadcast) -> int:
        """Broadcast a retention alert payload to all connected clients."""
        return await self.broadcast(alert.model_dump(mode="json"))

    async def disconnect_all(self) -> None:
        """Close all active WebSocket connections."""
        async with self._lock:
            connections = list(self._connections.items())
            self._connections.clear()
        for connection_id, websocket in connections:
            try:
                await websocket.close()
            except Exception:
                logger.warning("websocket_close_failed", connection_id=connection_id)

    @staticmethod
    def utc_now() -> datetime:
        return datetime.now(UTC)
