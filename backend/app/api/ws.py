import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.task_manager import progress_store

router = APIRouter()


@router.websocket("/ws/progress/{task_id}")
async def ws_progress(websocket: WebSocket, task_id: str):
    await websocket.accept()
    try:
        while True:
            info = progress_store.get(task_id, {"progress": 0, "status": "pending"})
            await websocket.send_json(info)
            if info.get("status") in ("completed", "failed"):
                break
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass
