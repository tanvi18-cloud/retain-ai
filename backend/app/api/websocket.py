"""WebSocket alert streaming routes."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.websocket_manager import WebSocketManager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/alerts")
async def alerts_websocket(websocket: WebSocket) -> None:
    """Stream live retention alerts to connected RM clients."""
    manager: WebSocketManager = websocket.app.state.websocket_manager
    connection_id = await manager.connect(websocket)
    await websocket.send_json(
        {
            "type": "CONNECTED",
            "message": "Connected to RetainAI alerts",
            "timestamp": manager.utc_now().isoformat(),
        }
    )
    try:
        while True:
            message = await websocket.receive_json()
            if isinstance(message, dict) and message.get("type") == "PING":
                await websocket.send_json(
                    {
                        "type": "PONG",
                        "timestamp": manager.utc_now().isoformat(),
                    }
                )
    except WebSocketDisconnect:
        await manager.disconnect(connection_id)
    except Exception:
        await manager.disconnect(connection_id)
        raise
