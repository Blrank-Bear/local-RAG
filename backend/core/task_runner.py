"""Autonomous multi-step task runner with progress tracking."""
import asyncio
import uuid
from datetime import datetime
from typing import Callable, Optional

from backend.agents.planner import PlannerAgent
from backend.agents.retriever import RetrieverAgent
from backend.agents.analyzer import AnalyzerAgent
from backend.agents.executor import ExecutorAgent
from backend.tools.registry import tool_registry


class TaskStep:
    def __init__(self, step_id: int, description: str, agent: str, parallel: bool = False):
        self.step_id = step_id
        self.description = description
        self.agent = agent
        self.parallel = parallel
        self.status = "pending"
        self.result = None
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "description": self.description,
            "agent": self.agent,
            "parallel": self.parallel,
            "status": self.status,
            "result": self.result,
        }


class TaskRunner:
    def __init__(self):
        self.planner = PlannerAgent()
        self.retriever = RetrieverAgent()
        self.analyzer = AnalyzerAgent()
        self.executor = ExecutorAgent()
        self._agent_map = {
            "planner": self.planner,
            "retriever": self.retriever,
            "analyzer": self.analyzer,
            "executor": self.executor,
        }

    async def execute_task(
        self,
        query: str,
        session_id: str,
        on_progress: Optional[Callable] = None,
    ) -> dict:
        task_id = str(uuid.uuid4())
        base_context = {
            "query": query,
            "session_id": session_id,
            "available_tools": tool_registry.list_tools(),
            "conversation_history": [],
        }

        # Plan
        context = await self.planner.run(base_context.copy())
        plan = context.get("plan", {})
        raw_steps = plan.get("steps", [])

        steps = [
            TaskStep(s["id"], s["description"], s.get("agent", "executor"), s.get("parallel", False))
            for s in raw_steps
        ]

        if on_progress:
            await on_progress({"task_id": task_id, "total_steps": len(steps), "status": "started"})

        # Group sequential vs parallel
        i = 0
        while i < len(steps):
            step = steps[i]
            if step.parallel:
                # Collect all consecutive parallel steps
                parallel_group = [step]
                j = i + 1
                while j < len(steps) and steps[j].parallel:
                    parallel_group.append(steps[j])
                    j += 1

                await asyncio.gather(*[
                    self._run_step(s, base_context, on_progress)
                    for s in parallel_group
                ])
                i = j
            else:
                await self._run_step(step, base_context, on_progress)
                i += 1

        # Final execution pass
        base_context = await self.retriever.run(base_context)
        base_context = await self.analyzer.run(base_context)
        base_context = await self.executor.run(base_context)

        if on_progress:
            await on_progress({"task_id": task_id, "status": "completed"})

        return {
            "task_id": task_id,
            "steps": [s.to_dict() for s in steps],
            "final_response": base_context.get("final_response", ""),
            "analysis": base_context.get("analysis", {}),
        }

    async def _run_step(
        self,
        step: TaskStep,
        context: dict,
        on_progress: Optional[Callable],
    ):
        step.status = "running"
        step.started_at = datetime.utcnow()

        if on_progress:
            await on_progress({"step": step.to_dict(), "status": "running"})

        agent = self._agent_map.get(step.agent, self.executor)
        step_context = context.copy()
        step_context["query"] = step.description

        try:
            result_ctx = await agent.run(step_context)
            step.result = result_ctx.get("final_response") or result_ctx.get("retrieved_summary", "")
            step.status = "completed"
        except Exception as e:
            step.result = str(e)
            step.status = "failed"

        step.completed_at = datetime.utcnow()

        if on_progress:
            await on_progress({"step": step.to_dict(), "status": step.status})


task_runner = TaskRunner()
