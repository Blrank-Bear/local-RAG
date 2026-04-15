"""Memory agent — manages conversation history backed by the PostgreSQL messages table."""
from typing import List

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.base_agent import BaseAgent
from backend.db.database import AsyncSessionLocal
from backend.db.models import Message

MAX_HISTORY = 20  # max turns fed into the LLM context window


class MemoryAgent(BaseAgent):
    name = "memory"
    role = "Manages conversation history and session context (DB-backed)"

    async def run(self, context: dict) -> dict:
        session_id = context.get("session_id", "default")
        action = context.get("memory_action", "load")

        if action == "load":
            context["conversation_history"] = await self._load(session_id)

        elif action == "save":
            query = context.get("query")
            response = context.get("final_response")
            await self._save(session_id, query, response)
            # Also refresh the in-context history so callers see the latest
            context["conversation_history"] = await self._load(session_id)

        elif action == "clear":
            await self._clear(session_id)
            context["conversation_history"] = []

        return context

    # ── DB helpers ─────────────────────────────────────────────────────────────

    async def _load(self, session_id: str) -> List[dict]:
        """Return the last MAX_HISTORY user/assistant messages for the session."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Message)
                .where(
                    Message.session_id == session_id,
                    Message.role.in_(["user", "assistant"]),
                )
                .order_by(Message.created_at.asc())
            )
            messages = result.scalars().all()

        # Keep only the last MAX_HISTORY entries for the LLM context
        tail = messages[-MAX_HISTORY:]
        return [{"role": m.role, "content": m.content} for m in tail]

    async def _save(self, session_id: str, query: str | None, response: str | None) -> None:
        """Persist a user+assistant turn. The chat route already writes the rows,
        so this is a no-op — history is read directly from the messages table."""
        # Messages are written by the chat route; nothing to do here.
        pass

    async def _clear(self, session_id: str) -> None:
        """Delete all messages for a session."""
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Message).where(Message.session_id == session_id)
            )
            await db.commit()

    async def get_history(self, session_id: str) -> List[dict]:
        return await self._load(session_id)


# Singleton
memory_agent = MemoryAgent()
