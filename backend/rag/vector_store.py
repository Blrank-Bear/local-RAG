"""pgvector-backed vector store — replaces ChromaDB."""
from __future__ import annotations

import asyncio
from typing import List, Tuple

import numpy as np
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.db.database import AsyncSessionLocal
from backend.db.models import DocumentChunk, EMBEDDING_DIM


# ── Embeddings ─────────────────────────────────────────────────────────────────

def _get_embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(
        base_url=settings.ollama_base_url,
        model=settings.ollama_embedding_model,
    )


def _embed(texts: List[str]) -> List[List[float]]:
    """Synchronous embedding call (used from sync contexts)."""
    return _get_embeddings().embed_documents(texts)


async def _embed_async(texts: List[str]) -> List[List[float]]:
    """Async embedding — runs in thread pool to avoid blocking."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _embed, texts)


async def _embed_query_async(query: str) -> List[float]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _get_embeddings().embed_query, query)


# ── Write ──────────────────────────────────────────────────────────────────────

async def add_documents_async(
    chunks: List[Document],
    document_id: str | None = None,
) -> int:
    """Embed and store document chunks in PostgreSQL."""
    if not chunks:
        return 0

    texts = [c.page_content for c in chunks]
    embeddings = await _embed_async(texts)

    async with AsyncSessionLocal() as db:
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            row = DocumentChunk(
                document_id=document_id,
                content=chunk.page_content,
                source=chunk.metadata.get("source", "unknown"),
                file_type=chunk.metadata.get("file_type", "txt"),
                file_hash=chunk.metadata.get("file_hash"),
                embedding=emb,
                chunk_index=i,
            )
            db.add(row)
        await db.commit()

    return len(chunks)


def add_documents(chunks: List[Document], document_id: str | None = None) -> int:
    """Sync wrapper — runs the async version in a new event loop if needed."""
    try:
        loop = asyncio.get_running_loop()
        # We're inside an async context — schedule as a task
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, add_documents_async(chunks, document_id))
            return future.result()
    except RuntimeError:
        return asyncio.run(add_documents_async(chunks, document_id))


# ── Read ───────────────────────────────────────────────────────────────────────

async def similarity_search_with_score_async(
    query: str,
    k: int = 5,
) -> List[Tuple[Document, float]]:
    """Return top-k chunks with cosine similarity scores."""
    query_emb = await _embed_query_async(query)
    emb_str = "[" + ",".join(str(x) for x in query_emb) + "]"

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text(
                """
                SELECT id, content, source, file_type,
                       1 - (embedding <=> :emb ::vector) AS score
                FROM document_chunks
                ORDER BY embedding <=> :emb ::vector
                LIMIT :k
                """
            ),
            {"emb": emb_str, "k": k},
        )
        rows = result.fetchall()

    output: List[Tuple[Document, float]] = []
    for row in rows:
        doc = Document(
            page_content=row.content,
            metadata={"source": row.source, "file_type": row.file_type},
        )
        output.append((doc, float(row.score)))

    return output


def similarity_search_with_score(
    query: str,
    k: int = 5,
) -> List[Tuple[Document, float]]:
    """Sync wrapper for similarity search."""
    try:
        loop = asyncio.get_running_loop()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, similarity_search_with_score_async(query, k))
            return future.result()
    except RuntimeError:
        return asyncio.run(similarity_search_with_score_async(query, k))


async def similarity_search_async(query: str, k: int = 5) -> List[Document]:
    results = await similarity_search_with_score_async(query, k)
    return [doc for doc, _ in results]


def similarity_search(query: str, k: int = 5) -> List[Document]:
    results = similarity_search_with_score(query, k)
    return [doc for doc, _ in results]


async def delete_chunks_by_document(document_id: str) -> None:
    """Remove all chunks belonging to a document."""
    async with AsyncSessionLocal() as db:
        await db.execute(
            text("DELETE FROM document_chunks WHERE document_id = :doc_id"),
            {"doc_id": document_id},
        )
        await db.commit()
