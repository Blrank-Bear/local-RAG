"""Memory agent — manages conversation history and session context."""
from typing import List
from backend.agents.base_agent import BaseAgent

MAX_HISTORY = 20


class MemoryAgent(BaseAgent):
    name = "memory"
    role = "Manages conversation history and session context"

    def __init__(self):
        self._sessions: dict[str, List[dict]] = {}

    async def run(self, context: dict) -> dict:
        session_id = context.get("session_id", "default")
        action = context.get("memory_action", "load")

        if action == "load":
            context["conversation_history"] = self._sessions.get(session_id, [])

        elif action == "save":
            history = self._sessions.setdefault(session_id, [])
            query = context.get("query")
            response = context.get("final_response")
            if query:
                history.append({"role": "user", "content": query})
            if response:
                history.append({"role": "assistant", "content": response})
            # Keep only last N messages
            self._sessions[session_id] = history[-MAX_HISTORY:]

        elif action == "clear":
            self._sessions.pop(session_id, None)

        return context

    def get_history(self, session_id: str) -> List[dict]:
        return self._sessions.get(session_id, [])


# Singleton
memory_agent = MemoryAgent()
