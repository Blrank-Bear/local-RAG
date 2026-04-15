"""Document ingestion routes."""
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.db.database import get_db
from backend.db.models import Document
from backend.rag.ingestion import ingest_file
from backend.rag.vector_store import add_documents

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".pdf", ".txt"):
        raise HTTPException(400, "Only PDF and TXT files are supported.")

    settings.docs_dir.mkdir(parents=True, exist_ok=True)
    dest = settings.docs_dir / file.filename

    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    chunks = ingest_file(dest)
    count = add_documents(chunks)

    doc = Document(
        filename=file.filename,
        file_type=suffix.lstrip("."),
        chunk_count=count,
    )
    db.add(doc)
    await db.flush()

    return {"filename": file.filename, "chunks_indexed": count, "document_id": doc.id}


@router.get("/")
async def list_documents(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    result = await db.execute(select(Document).where(Document.is_active == True))
    docs = result.scalars().all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "file_type": d.file_type,
            "chunk_count": d.chunk_count,
            "ingested_at": d.ingested_at.isoformat(),
        }
        for d in docs
    ]
