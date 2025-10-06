"""WebSocket handler for real-time notifications."""
from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..state import get_notifier

router = APIRouter()


@router.websocket("/ws/notifications")
async def notifications_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    notifier = get_notifier()

    def push(event: dict) -> None:
        try:
            websocket.send_json(event)
        except RuntimeError:
            pass

    notifier.subscribe("message_created", push)
    notifier.subscribe("dialog_status", push)
    notifier.subscribe("dialog_assigned", push)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        return
