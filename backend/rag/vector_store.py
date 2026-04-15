"""
Vector store backed by PostgreSQL.

Strategy:
  - If pgvector extension is available → uses native vector column + HNSW index (fast).
  - If pgvector is NOT available → falls back to storing embeddings as JSON and doing
    cosine similarity in Python (works on any PostgreSQL, slower for large corpora).

The fallback is transparent — no code changes needed elsewhere.
"""
from __future__ import annotations

import asyncio
import json
import math
from typing import List, Tuple

from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from sqlalchemy import select, text

from backend.config import settings
from backend.db.database import AsyncSessionLocal

# ── Runtime flag: set once on first use ───────────────────────────────────────
_pgvector_available: bool | None = None


async def _check_pgvector() -> bool:
    """
    Test whether the pgvector extension is available.
    Uses its own isolated engine connection so a failure never
    aborts the session that will be used for actual inserts.
    Cached after the first call.
    """
    global _pgvector_available
    if _pgvector_available is not None:
        return _pgvector_available

    from backend.db.database import engine
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT '[1,2,3]'::vector"))
        _pgvector_available = True
    except Exception:
        _pgvector_available = False

    return _pgvector_available


# ── Embeddings ─────────────────────────────────────────────────────────────────

def _get_embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(
        base_url=settings.ollama_base_url,
        model=settings.ollama_embedding_model,
    )


async def _embed_async(texts: List[str]) -> List[List[float]]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _get_embeddings().embed_documents, texts)


async def _embed_query_async(query: str) -> List[float]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _get_embeddings().embed_query, query)


# ── Cosine similarity (Python fallback) ───────────────────────────────────────

def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


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

    use_pgvector = await _check_pgvector()

    async with AsyncSessionLocal() as db:
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            if use_pgvector:
                emb_str = "[" + ",".join(str(x) for x in emb) + "]"
                await db.execute(
                    text("""
                        INSERT INTO document_chunks
                            (id, document_id, content, source, file_type, file_hash,
                             embedding, chunk_index, created_at)
                        VALUES (
                            gen_random_uuid()::text, :doc_id, :content, :source,
                            :file_type, :file_hash, :emb::vector, :idx, NOW()
                        )
                    """),
                    {
                        "doc_id": document_id,
                        "content": chunk.page_content,
                        "source": chunk.metadata.get("source", "unknown"),
                        "file_type": chunk.metadata.get("file_type", "txt"),
                        "file_hash": chunk.metadata.get("file_hash"),
                        "emb": emb_str,
                        "idx": i,
                    },
                )
            else:
                # Fallback: store embedding as JSON text
                await db.execute(
                    text("""
                        INSERT INTO document_chunks
                            (id, document_id, content, source, file_type, file_hash,
                             embedding_json, chunk_index, created_at)
                        VALUES (
                            gen_random_uuid()::text, :doc_id, :content, :source,
                            :file_type, :file_hash, :emb_json, :idx, NOW()
                        )
                    """),
                    {
                        "doc_id": document_id,
                        "content": chunk.page_content,
                        "source": chunk.metadata.get("source", "unknown"),
                        "file_type": chunk.metadata.get("file_type", "txt"),
                        "file_hash": chunk.metadata.get("file_hash"),
                        "emb_json": json.dumps(emb),
                        "idx": i,
                    },
                )
        await db.commit()

    return len(chunks)


def add_documents(chunks: List[Document], document_id: str | None = None) -> int:
    """Sync wrapper."""
    try:
        loop = asyncio.get_running_loop()
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
    use_pgvector = await _check_pgvector()

    async with AsyncSessionLocal() as db:
        if use_pgvector:
            emb_str = "[" + ",".join(str(x) for x in query_emb) + "]"
            result = await db.execute(
                text("""
                    SELECT content, source, file_type,
                           1 - (embedding <=> :emb::vector) AS score
                    FROM document_chunks
                    ORDER BY embedding <=> :emb::vector
                    LIMIT :k
                """),
                {"emb": emb_str, "k": k},
            )
            rows = result.fetchall()
            return [
                (
                    Document(
                        page_content=row.content,
                        metadata={"source": row.source, "file_type": row.file_type},
                    ),
                    float(row.score),
                )
                for row in rows
            ]
        else:
            # Fallback: load all embeddings and rank in Python
            result = await db.execute(
                text("SELECT content, source, file_type, embedding_json FROM document_chunks")
            )
            rows = result.fetchall()

            scored: List[Tuple[Document, float]] = []
            for row in rows:
                if not row.embedding_json:
                    continue
                emb = json.loads(row.embedding_json)
                score = _cosine_similarity(query_emb, emb)
                doc = Document(
                    page_content=row.content,
                    metadata={"source": row.source, "file_type": row.file_type},
                )
                scored.append((doc, score))

            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[:k]


def similarity_search_with_score(
    query: str,
    k: int = 5,
) -> List[Tuple[Document, float]]:
    """Sync wrapper."""
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
    async with AsyncSessionLocal() as db:
        await db.execute(
            text("DELETE FROM document_chunks WHERE document_id = :doc_id"),
            {"doc_id": document_id},
        )
        await db.commit()
