"""Feedback and evaluation routes."""
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.memory.feedback_store import feedback_store

router = APIRouter(prefix="/feedback", tags=["feedback"])


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


@router.post("/")
async def submit_feedback(req: FeedbackRequest, db: AsyncSession = Depends(get_db)):
    fb = await feedback_store.save_feedback(
        db, req.session_id, req.message_id, req.rating, req.comment
    )
    return {"feedback_id": fb.id, "status": "saved"}


@router.post("/evaluate")
async def evaluate_response(req: EvaluateRequest, db: AsyncSession = Depends(get_db)):
    log = await feedback_store.evaluate_response(
        db, req.session_id, req.query, req.response, req.retrieved_docs
    )
    return {
        "evaluation_id": log.id,
        "relevance_score": log.relevance_score,
        "faithfulness_score": log.faithfulness_score,
    }


@router.get("/stats/{session_id}")
async def session_stats(session_id: str, db: AsyncSession = Depends(get_db)):
    return await feedback_store.get_session_stats(db, session_id)
