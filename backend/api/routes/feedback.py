"""Feedback and evaluation routes."""
from typing import Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.memory.feedback_store import feedback_store
from backend.api.deps import get_current_user
from backend.db.models import User

router = APIRouter(prefix="/feedback", tags=["feedback"])


# ── Schemas ────────────────────────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    session_id: str
    message_id: Optional[str] = None
    rating: Optional[int] = None   # 1-5
    comment: Optional[str] = None


class EvaluateRequest(BaseModel):
    session_id: str
    query: str
    response: str
    retrieved_docs: list = []


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/")
async def submit_feedback(
    req: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Block duplicate ratings on the same message
    if req.message_id and req.rating is not None:
        existing = await feedback_store.get_existing_feedback(db, req.session_id, req.message_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This message has already been rated.",
            )

    fb = await feedback_store.save_feedback(
        db, req.session_id, req.message_id, req.rating, req.comment
    )
    return {"feedback_id": fb.id, "status": "saved"}


@router.get("/rated/{session_id}", response_model=Dict[str, int])
async def get_rated_messages(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns a map of { message_id: rating } for every message
    in this session that has already been rated.
    The frontend uses this to restore rated state after a page reload.
    """
    return await feedback_store.get_rated_messages(db, session_id)


@router.post("/evaluate")
async def evaluate_response(
    req: EvaluateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log = await feedback_store.evaluate_response(
        db, req.session_id, req.query, req.response, req.retrieved_docs
    )
    return {
        "evaluation_id": log.id,
        "relevance_score": log.relevance_score,
        "faithfulness_score": log.faithfulness_score,
    }


@router.get("/stats/{session_id}")
async def session_stats(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await feedback_store.get_session_stats(db, session_id)
