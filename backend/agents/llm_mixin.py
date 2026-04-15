"""Shared LLM access mixin for all agents."""
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from backend.config import settings


class LLMMixin:
    def _get_llm(self, temperature: float = 0.3) -> ChatOllama:
        return ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=temperature,
        )

    async def _chat(self, system: str, user: str, temperature: float = 0.3) -> str:
        llm = self._get_llm(temperature)
        messages = [SystemMessage(content=system), HumanMessage(content=user)]
        response = await llm.ainvoke(messages)
        return response.content.strip()
