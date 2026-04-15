"""Autonomous task execution routes."""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import json

from backend.core.task_runner import task_runner

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


@router.post("/run")
async def run_task(req: TaskRequest):
    session_id = req.session_id or str(uuid.uuid4())
    result = await task_runner.execute_task(req.query, session_id)
    return result


@router.websocket("/ws/{session_id}")
async def task_ws(websocket: WebSocket, session_id: str):
    """Stream task progress over WebSocket."""
    await websocket.accept()
    try:
        data = await websocket.receive_text()
        payload = json.loads(data)
        query = payload.get("query", "")

        async def on_progress(update: dict):
            await websocket.send_text(json.dumps(update))

        result = await task_runner.execute_task(query, session_id, on_progress=on_progress)
        await websocket.send_text(json.dumps({"type": "completed", "result": result}))

    except WebSocketDisconnect:
        pass
