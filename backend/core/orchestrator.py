"""Central orchestrator — single LLM call for speed, full pipeline for complex queries."""
import asyncio
from typing import AsyncGenerator

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

from backend.agents.memory_agent import memory_agent
from backend.rag.vector_store import similarity_search_with_score
from backend.config import settings


def _get_llm():
    return ChatOllama(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        temperature=0.4,
    )


class Orchestrator:

    async def run(
        self,
        query: str,
        session_id: str,
        on_status=None,
    ) -> dict:
        async def emit(status: str, agent: str = ""):
            if on_status:
                await on_status({"status": status, "agent": agent})

        # Load conversation history
        await emit("Loading memory...", "memory")
        context = {"query": query, "session_id": session_id, "memory_action": "load"}
        context = await memory_agent.run(context)
        history = context.get("conversation_history", [])

        # RAG retrieval
        await emit("Retrieving knowledge...", "retriever")
        retrieved = []
        retrieved_summary = ""
        try:
            results = similarity_search_with_score(query, k=4)
            retrieved = [
                {"content": doc.page_content, "source": doc.metadata.get("source", ""), "score": round(float(s), 4)}
                for doc, s in results
            ]
            if retrieved:
                retrieved_summary = "\n\n".join(
                    f"[{r['source']}]\n{r['content']}" for r in retrieved[:3]
                )
        except Exception:
            pass  # No docs indexed yet — that's fine

        # Build prompt
        await emit("Generating response...", "executor")

        system = """You are a helpful, knowledgeable AI assistant. 
Answer clearly and concisely. Use the provided context if relevant.
If context is provided, cite the source. If not relevant, answer from your knowledge."""

        context_block = f"\n\nRelevant context:\n{retrieved_summary}" if retrieved_summary else ""

        history_block = ""
        if history:
            history_block = "\n\nConversation history:\n" + "\n".join(
                f"{m['role'].upper()}: {m['content']}" for m in history[-6:]
            )

        user_msg = f"{query}{context_block}{history_block}"

        # Single LLM call
        llm = _get_llm()
        response = await asyncio.wait_for(
            llm.ainvoke([SystemMessage(content=system), HumanMessage(content=user_msg)]),
            timeout=120,
        )
        final_response = response.content.strip()

        # Save to memory
        context["final_response"] = final_response
        context["memory_action"] = "save"
        context = await memory_agent.run(context)

        await emit("Done", "orchestrator")

        return {
            "query": query,
            "session_id": session_id,
            "final_response": final_response,
            "retrieved_context": retrieved,
            "analysis": {},
            "plan": {},
        }

    async def stream(
        self,
        query: str,
        session_id: str,
    ) -> AsyncGenerator[dict, None]:
        updates = []

        async def collect(update: dict):
            updates.append(update)

        try:
            context = await self.run(query, session_id, on_status=collect)
        except asyncio.TimeoutError:
            yield {"type": "error", "message": "Request timed out. Ollama may be busy — please try again."}
            return
        except Exception as e:
            yield {"type": "error", "message": str(e)}
            return

        for update in updates:
            yield {"type": "status", **update}

        yield {
            "type": "response",
            "content": context.get("final_response", ""),
            "analysis": context.get("analysis", {}),
            "retrieved_context": context.get("retrieved_context", []),
            "plan": context.get("plan", {}),
        }


orchestrator = Orchestrator()
