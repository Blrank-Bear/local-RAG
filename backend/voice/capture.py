"""Microphone capture — push-to-talk and continuous modes."""
import threading
import queue
from typing import Callable, Optional

import numpy as np
import sounddevice as sd

from backend.config import settings

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "float32"
BLOCK_SIZE = 1024


class AudioCapture:
    """Captures microphone audio and emits numpy chunks via callback."""

    def __init__(self, on_audio: Callable[[np.ndarray], None]):
        self._on_audio = on_audio
        self._stream: Optional[sd.InputStream] = None
        self._running = False

    def _callback(self, indata: np.ndarray, frames: int, time, status):
        if status:
            pass  # log if needed
        self._on_audio(indata.copy().flatten())

    def start(self):
        self._running = True
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE,
            blocksize=BLOCK_SIZE,
            callback=self._callback,
        )
        self._stream.start()

    def stop(self):
        self._running = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None


class PushToTalkRecorder:
    """Records audio while active; returns full recording on stop."""

    def __init__(self):
        self._buffer: list[np.ndarray] = []
        self._capture = AudioCapture(on_audio=self._collect)
        self._recording = False

    def _collect(self, chunk: np.ndarray):
        if self._recording:
            self._buffer.append(chunk)

    def start_recording(self):
        self._buffer = []
        self._recording = True
        self._capture.start()

    def stop_recording(self) -> np.ndarray:
        self._recording = False
        self._capture.stop()
        if not self._buffer:
            return np.array([], dtype=np.float32)
        return np.concatenate(self._buffer)


class ContinuousListener:
    """Continuously listens and emits utterances based on silence detection."""

    SILENCE_THRESHOLD = 0.01
    SILENCE_FRAMES = 30  # ~1.9s of silence triggers utterance

    def __init__(self, on_utterance: Callable[[np.ndarray], None]):
        self._on_utterance = on_utterance
        self._buffer: list[np.ndarray] = []
        self._silence_count = 0
        self._capture = AudioCapture(on_audio=self._process)

    def _process(self, chunk: np.ndarray):
        rms = float(np.sqrt(np.mean(chunk ** 2)))
        if rms > self.SILENCE_THRESHOLD:
            self._buffer.append(chunk)
            self._silence_count = 0
        elif self._buffer:
            self._silence_count += 1
            if self._silence_count >= self.SILENCE_FRAMES:
                audio = np.concatenate(self._buffer)
                self._buffer = []
                self._silence_count = 0
                self._on_utterance(audio)

    def start(self):
        self._capture.start()

    def stop(self):
        self._capture.stop()
