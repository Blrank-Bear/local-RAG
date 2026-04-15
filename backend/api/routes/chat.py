"""Chat routes — HTTP only."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.orchestrator import orchestrator
from backend.db.database import get_db
from backend.db.models import Session, Message

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    message_id: str
    response: str
    retrieved_context: list


@router.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    session_id = req.session_id or str(uuid.uuid4())

    session = await db.get(Session, session_id)
    if not session:
        session = Session(id=session_id)
        db.add(session)
        await db.flush()

    context = await orchestrator.run(req.query, session_id)

    user_msg = Message(session_id=session_id, role="user", content=req.query)
    assistant_msg = Message(
        session_id=session_id,
        role="assistant",
        content=context.get("final_response", ""),
        retrieved_context=context.get("retrieved_context", []),
    )
    db.add(user_msg)
    db.add(assistant_msg)
    await db.flush()

    return ChatResponse(
        session_id=session_id,
        message_id=assistant_msg.id,
        response=context.get("final_response", ""),
        retrieved_context=context.get("retrieved_context", []),
    )
