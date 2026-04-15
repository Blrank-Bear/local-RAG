"""Analyzer agent — performs structured analysis on retrieved context."""
import json
from backend.agents.base_agent import BaseAgent
from backend.agents.llm_mixin import LLMMixin

SYSTEM_PROMPT = """You are an Analyzer agent. Your job is to perform structured analysis
on the provided context and query.

Return your analysis as JSON:
{
  "key_findings": ["finding 1", "finding 2", ...],
  "reasoning": "step-by-step reasoning",
  "confidence": 0.0-1.0,
  "gaps": ["missing info 1", ...],
  "recommendation": "what to do next"
}"""


class AnalyzerAgent(BaseAgent, LLMMixin):
    name = "analyzer"
    role = "Performs structured analysis and reasoning on context"

    async def run(self, context: dict) -> dict:
        query = context.get("query", "")
        retrieved_summary = context.get("retrieved_summary", "No context available.")
        history = context.get("conversation_history", [])

        history_str = ""
        if history:
            history_str = "\n".join(
                f"{m['role'].upper()}: {m['content']}" for m in history[-6:]
            )

        user_prompt = f"""Query: {query}

Retrieved context:
{retrieved_summary}

Conversation history:
{history_str}

Perform a structured analysis."""

        raw = await self._chat(SYSTEM_PROMPT, user_prompt, temperature=0.2)

        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        try:
            analysis = json.loads(raw)
        except json.JSONDecodeError:
            analysis = {
                "key_findings": [],
                "reasoning": raw,
                "confidence": 0.5,
                "gaps": [],
                "recommendation": "Proceed with available information",
            }

        context["analysis"] = analysis
        return context
