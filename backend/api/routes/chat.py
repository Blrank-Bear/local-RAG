"""Chat routes — messaging, history, and session management."""
import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.orchestrator import orchestrator
from backend.db.database import get_db
from backend.db.models import Session, Message, User, SessionStatus
from backend.api.deps import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])


# ── Schemas ────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    message_id: str
    response: str
    retrieved_context: list


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    retrieved_context: Optional[list] = None
    created_at: str


class SessionOut(BaseModel):
    id: str
    created_at: str
    updated_at: str
    status: str
    message_count: int
    last_message: Optional[str] = None


# ── Chat ───────────────────────────────────────────────────────────────────────

@router.post("/", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session_id = req.session_id or str(uuid.uuid4())

    session = await db.get(Session, session_id)
    if not session:
        session = Session(id=session_id, user_id=current_user.id)
        db.add(session)
        await db.flush()
    elif session.user_id != current_user.id:
        raise HTTPException(403, "Not your session.")

    context = await orchestrator.run(req.query, session_id)

    # Persist both turns
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


# ── History ────────────────────────────────────────────────────────────────────

@router.get("/history/{session_id}", response_model=List[MessageOut])
async def get_history(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all messages for a session, oldest first."""
    session = await db.get(Session, session_id)
    if not session:
        raise HTTPException(404, "Session not found.")
    if session.user_id != current_user.id:
        raise HTTPException(403, "Not your session.")

    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()

    return [
        MessageOut(
            id=m.id,
            role=m.role,
            content=m.content,
            retrieved_context=m.retrieved_context or [],
            created_at=m.created_at.isoformat(),
        )
        for m in messages
    ]


@router.delete("/history/{session_id}", status_code=204)
async def delete_history(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete all messages in a session (keeps the session row itself)."""
    session = await db.get(Session, session_id)
    if not session:
        raise HTTPException(404, "Session not found.")
    if session.user_id != current_user.id:
        raise HTTPException(403, "Not your session.")

    await db.execute(
        delete(Message).where(Message.session_id == session_id)
    )


# ── Sessions ───────────────────────────────────────────────────────────────────

@router.get("/sessions", response_model=List[SessionOut])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all sessions for the current user, newest first."""
    result = await db.execute(
        select(Session)
        .where(Session.user_id == current_user.id)
        .order_by(Session.updated_at.desc())
    )
    sessions = result.scalars().all()

    out = []
    for s in sessions:
        # Fetch message count + last message preview
        msgs_result = await db.execute(
            select(Message)
            .where(Message.session_id == s.id)
            .order_by(Message.created_at.desc())
        )
        msgs = msgs_result.scalars().all()
        last_msg = msgs[0].content[:80] if msgs else None

        out.append(SessionOut(
            id=s.id,
            created_at=s.created_at.isoformat(),
            updated_at=s.updated_at.isoformat(),
            status=s.status.value,
            message_count=len(msgs),
            last_message=last_msg,
        ))

    return out


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a session and all its messages."""
    session = await db.get(Session, session_id)
    if not session:
        raise HTTPException(404, "Session not found.")
    if session.user_id != current_user.id:
        raise HTTPException(403, "Not your session.")

    await db.delete(session)  # cascade deletes messages via FK
