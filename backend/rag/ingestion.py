"""Document ingestion pipeline for PDF and TXT files."""
import hashlib
from pathlib import Path
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document

from backend.config import settings


def _file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def load_documents(file_path: Path) -> List[Document]:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        loader = PyPDFLoader(str(file_path))
    elif suffix == ".txt":
        loader = TextLoader(str(file_path), encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {suffix}")
    return loader.load()


def split_documents(docs: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_documents(docs)


def ingest_file(file_path: Path) -> List[Document]:
    """Load, split and return chunks with metadata."""
    raw = load_documents(file_path)
    chunks = split_documents(raw)
    file_hash = _file_hash(file_path)
    for chunk in chunks:
        chunk.metadata.update(
            {
                "source": file_path.name,
                "file_type": file_path.suffix.lstrip("."),
                "file_hash": file_hash,
            }
        )
    return chunks
