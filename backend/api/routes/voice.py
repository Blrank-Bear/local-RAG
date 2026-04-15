"""Voice routes — HTTP multipart audio upload."""
import io
import tempfile
from pathlib import Path

import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from backend.voice.stt import transcribe_file
from backend.api.deps import get_current_user
from backend.db.models import User

router = APIRouter(prefix="/voice", tags=["voice"])


class TranscribeResponse(BaseModel):
    transcript: str


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Accept a WAV/WebM/OGG audio file, return the transcript.
    The browser records via MediaRecorder and POSTs the blob here.
    """
    suffix = Path(file.filename or "audio.webm").suffix or ".webm"
    allowed = {".wav", ".webm", ".ogg", ".mp3", ".m4a", ".mp4"}
    if suffix.lower() not in allowed:
        raise HTTPException(400, f"Unsupported audio format: {suffix}")

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    try:
        transcript = transcribe_file(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    return TranscribeResponse(transcript=transcript.strip())
