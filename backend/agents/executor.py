"""Executor agent — runs tools and generates the final response."""
from backend.agents.base_agent import BaseAgent
from backend.agents.llm_mixin import LLMMixin
from backend.tools.registry import tool_registry

SYSTEM_PROMPT = """You are an Executor agent. You have access to tools and must produce
a clear, helpful, and accurate final response to the user.

Use the analysis and retrieved context to craft your answer.
Be direct, structured, and cite sources when relevant."""


class ExecutorAgent(BaseAgent, LLMMixin):
    name = "executor"
    role = "Executes tools and generates the final user-facing response"

    async def run(self, context: dict) -> dict:
        query = context.get("query", "")
        analysis = context.get("analysis", {})
        retrieved_summary = context.get("retrieved_summary", "")
        plan = context.get("plan", {})
        tool_results = []

        # Execute any tool calls specified in the plan steps
        steps = plan.get("steps", [])
        for step in steps:
            tool_name = step.get("tool")
            tool_args = step.get("tool_args", {})
            if tool_name:
                result = await tool_registry.run(tool_name, **tool_args)
                tool_results.append({"tool": tool_name, "result": result})

        context["tool_results"] = tool_results

        reasoning = analysis.get("reasoning", "")
        findings = "\n".join(f"- {f}" for f in analysis.get("key_findings", []))
        tools_str = "\n".join(
            f"[{r['tool']}]: {r['result']}" for r in tool_results
        ) if tool_results else "No tools executed."

        user_prompt = f"""User query: {query}

Retrieved knowledge:
{retrieved_summary}

Analysis findings:
{findings}

Reasoning:
{reasoning}

Tool results:
{tools_str}

Generate a comprehensive, well-structured final response:"""

        response = await self._chat(SYSTEM_PROMPT, user_prompt, temperature=0.4)
        context["final_response"] = response
        return context
