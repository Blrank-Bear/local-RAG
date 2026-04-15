"""RAG search tool — queries the vector store."""
from typing import Any, List

from backend.tools.base import BaseTool
from backend.rag.vector_store import similarity_search_with_score


class RAGSearchTool(BaseTool):
    name = "rag_search"
    description = "Search the knowledge base for relevant document chunks."

    async def run(self, query: str, k: int = 5) -> List[dict]:
        results = similarity_search_with_score(query, k=k)
        return [
            {
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "score": round(float(score), 4),
            }
            for doc, score in results
        ]
