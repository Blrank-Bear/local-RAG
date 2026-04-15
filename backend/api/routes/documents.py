"""Document ingestion routes."""
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.db.database import get_db
from backend.db.models import Document
from backend.rag.ingestion import ingest_file
from backend.rag.vector_store import add_documents_async
from backend.api.deps import get_current_user
from backend.db.models import User

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".pdf", ".txt"):
        raise HTTPException(400, "Only PDF and TXT files are supported.")

    settings.docs_dir.mkdir(parents=True, exist_ok=True)
    dest = settings.docs_dir / file.filename

    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    # Create and COMMIT the Document row first so the FK in document_chunks resolves.
    # add_documents_async opens its own session, so the parent row must be visible.
    doc = Document(
        filename=file.filename,
        file_type=suffix.lstrip("."),
        chunk_count=0,
    )
    db.add(doc)
    await db.commit()   # ← commit here so add_documents_async can see doc.id

    try:
        chunks = ingest_file(dest, document_id=doc.id)
        count = await add_documents_async(chunks, document_id=doc.id)
    except Exception as e:
        # Roll back the document record if chunk ingestion fails
        await db.delete(doc)
        await db.commit()
        raise HTTPException(500, f"Ingestion failed: {e}")

    # Update chunk count
    doc.chunk_count = count
    db.add(doc)
    await db.commit()

    return {"filename": file.filename, "chunks_indexed": count, "document_id": doc.id}


@router.get("/")
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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
