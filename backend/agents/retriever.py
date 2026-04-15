"""Retriever agent — fetches relevant context from the vector store."""
from backend.agents.base_agent import BaseAgent
from backend.agents.llm_mixin import LLMMixin
from backend.tools.registry import tool_registry

SYSTEM_PROMPT = """You are a Retriever agent. Given a user query and retrieved document chunks,
synthesize the most relevant information into a concise context summary.
Focus on facts, avoid speculation."""


class RetrieverAgent(BaseAgent, LLMMixin):
    name = "retriever"
    role = "Retrieves and synthesizes relevant knowledge from documents"

    async def run(self, context: dict) -> dict:
        query = context.get("query", "")
        k = context.get("retrieval_k", 5)

        results = await tool_registry.run("rag_search", query=query, k=k)

        if not results or isinstance(results, dict) and "error" in results:
            context["retrieved_context"] = []
            context["retrieved_summary"] = "No relevant documents found."
            return context

        context["retrieved_context"] = results

        chunks_text = "\n\n".join(
            f"[Source: {r['source']} | Score: {r['score']}]\n{r['content']}"
            for r in results
        )

        summary = await self._chat(
            SYSTEM_PROMPT,
            f"Query: {query}\n\nRetrieved chunks:\n{chunks_text}\n\nSynthesize the key information:",
        )

        context["retrieved_summary"] = summary
        return context
