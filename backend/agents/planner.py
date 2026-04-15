"""Planner agent — breaks user requests into ordered steps."""
import json
from backend.agents.base_agent import BaseAgent
from backend.agents.llm_mixin import LLMMixin

SYSTEM_PROMPT = """You are a Planner agent. Your job is to decompose a user request into
a clear, ordered list of steps that other agents will execute.

Return ONLY valid JSON in this format:
{
  "steps": [
    {"id": 1, "description": "...", "agent": "retriever|analyzer|executor|memory", "parallel": false},
    ...
  ],
  "summary": "Brief plan summary"
}

Rules:
- Mark steps as parallel: true only if they are truly independent.
- Use the correct agent for each step.
- Be concise and specific."""


class PlannerAgent(BaseAgent, LLMMixin):
    name = "planner"
    role = "Decomposes complex requests into executable steps"

    async def run(self, context: dict) -> dict:
        query = context.get("query", "")
        available_tools = context.get("available_tools", [])
        tools_str = ", ".join(t["name"] for t in available_tools)

        user_prompt = f"""User request: {query}

Available tools: {tools_str}

Create a step-by-step plan."""

        raw = await self._chat(SYSTEM_PROMPT, user_prompt)

        # Extract JSON even if wrapped in markdown
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        try:
            plan = json.loads(raw)
        except json.JSONDecodeError:
            plan = {
                "steps": [{"id": 1, "description": query, "agent": "executor", "parallel": False}],
                "summary": "Direct execution",
            }

        context["plan"] = plan
        return context
