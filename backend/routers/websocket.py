import asyncio
import json
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from tasks.alignment_task import progress_store

router = APIRouter()

connections: Dict[str, Set[WebSocket]] = {}


@router.websocket("/ws/projects/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    await websocket.accept()
    if project_id not in connections:
        connections[project_id] = set()
    connections[project_id].add(websocket)

    try:
        while True:
            progress = progress_store.get(project_id, {"percent": 0, "stage": "waiting"})
            await websocket.send_json(progress)

            if progress.get("percent", 0) >= 100:
                break

            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
    finally:
        connections[project_id].discard(websocket)
