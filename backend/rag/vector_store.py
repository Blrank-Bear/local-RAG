"""ChromaDB vector store wrapper with Ollama embeddings."""
from pathlib import Path
from typing import List

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from backend.config import settings


def _get_embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(
        base_url=settings.ollama_base_url,
        model=settings.ollama_embedding_model,
    )


def _get_chroma_client() -> chromadb.ClientAPI:
    return chromadb.PersistentClient(
        path=str(settings.chroma_persist_dir),
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def get_vector_store(collection_name: str = "documents") -> Chroma:
    return Chroma(
        client=_get_chroma_client(),
        collection_name=collection_name,
        embedding_function=_get_embeddings(),
    )


def add_documents(chunks: List[Document], collection_name: str = "documents") -> int:
    store = get_vector_store(collection_name)
    store.add_documents(chunks)
    return len(chunks)


def similarity_search(
    query: str,
    k: int = 5,
    collection_name: str = "documents",
) -> List[Document]:
    store = get_vector_store(collection_name)
    return store.similarity_search(query, k=k)


def similarity_search_with_score(
    query: str,
    k: int = 5,
    collection_name: str = "documents",
) -> List[tuple[Document, float]]:
    store = get_vector_store(collection_name)
    return store.similarity_search_with_score(query, k=k)


def delete_collection(collection_name: str = "documents") -> None:
    client = _get_chroma_client()
    client.delete_collection(collection_name)
