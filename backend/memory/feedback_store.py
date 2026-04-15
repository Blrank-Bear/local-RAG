"""Feedback storage and quality evaluation."""
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import Feedback, EvaluationLog, Message
from backend.agents.llm_mixin import LLMMixin

EVAL_SYSTEM = """You are a response quality evaluator. Given a user query, retrieved context,
and the agent's response, score the following on a scale of 0.0 to 1.0:
- relevance: How relevant is the response to the query?
- faithfulness: Is the response grounded in the retrieved context?

Return ONLY JSON: {"relevance": 0.0, "faithfulness": 0.0}"""


class FeedbackStore(LLMMixin):
    async def save_feedback(
        self,
        db: AsyncSession,
        session_id: str,
        message_id: Optional[str],
        rating: Optional[int],
        comment: Optional[str],
    ) -> Feedback:
        fb = Feedback(
            session_id=session_id,
            message_id=message_id,
            rating=rating,
            comment=comment,
        )
        db.add(fb)
        await db.flush()
        return fb

    async def evaluate_response(
        self,
        db: AsyncSession,
        session_id: str,
        query: str,
        response: str,
        retrieved_docs: list,
    ) -> EvaluationLog:
        import json

        context_str = "\n".join(
            d.get("content", "") for d in retrieved_docs[:3]
        ) if retrieved_docs else "No context"

        raw = await self._chat(
            EVAL_SYSTEM,
            f"Query: {query}\n\nContext:\n{context_str}\n\nResponse:\n{response}",
            temperature=0.1,
        )

        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        try:
            scores = json.loads(raw)
        except Exception:
            scores = {"relevance": 0.5, "faithfulness": 0.5}

        log = EvaluationLog(
            session_id=session_id,
            query=query,
            response=response,
            retrieved_docs=retrieved_docs,
            relevance_score=scores.get("relevance", 0.5),
            faithfulness_score=scores.get("faithfulness", 0.5),
        )
        db.add(log)
        await db.flush()
        return log

    async def get_session_stats(self, db: AsyncSession, session_id: str) -> dict:
        result = await db.execute(
            select(Feedback).where(Feedback.session_id == session_id)
        )
        feedbacks = result.scalars().all()

        ratings = [f.rating for f in feedbacks if f.rating is not None]
        avg_rating = sum(ratings) / len(ratings) if ratings else None

        eval_result = await db.execute(
            select(EvaluationLog).where(EvaluationLog.session_id == session_id)
        )
        evals = eval_result.scalars().all()

        avg_relevance = (
            sum(e.relevance_score for e in evals if e.relevance_score) / len(evals)
            if evals else None
        )

        return {
            "session_id": session_id,
            "total_feedbacks": len(feedbacks),
            "average_rating": avg_rating,
            "average_relevance": avg_relevance,
            "total_evaluations": len(evals),
        }


feedback_store = FeedbackStore()
