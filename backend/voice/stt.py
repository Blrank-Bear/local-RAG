"""Speech-to-text using faster-whisper (local, CTranslate2-based)."""
from pathlib import Path
from typing import Optional

import numpy as np
from faster_whisper import WhisperModel

from backend.config import settings

_model: Optional[WhisperModel] = None


def get_model() -> WhisperModel:
    global _model
    if _model is None:
        _model = WhisperModel(
            settings.whisper_model,
            device="cpu",
            compute_type="int8",
        )
    return _model


def transcribe_numpy(audio: np.ndarray) -> str:
    """Transcribe a float32 numpy array (16kHz mono)."""
    model = get_model()
    segments, _ = model.transcribe(audio.astype(np.float32), beam_size=5)
    return " ".join(seg.text for seg in segments).strip()


def transcribe_audio_bytes(audio_bytes: bytes, sample_rate: int = 16000) -> str:
    """Transcribe raw PCM float32 bytes."""
    audio = np.frombuffer(audio_bytes, dtype=np.float32)
    return transcribe_numpy(audio)


def transcribe_file(file_path: Path) -> str:
    """Transcribe an audio file (wav/mp3/etc.)."""
    model = get_model()
    segments, _ = model.transcribe(str(file_path), beam_size=5)
    return " ".join(seg.text for seg in segments).strip()
