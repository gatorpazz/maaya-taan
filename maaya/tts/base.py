"""TTS backend interface plus a content-addressed disk cache."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Protocol

import numpy as np


class TTSBackend(Protocol):
    name: str
    sample_rate: int

    def synth(self, text: str, rate: float = 1.0) -> np.ndarray:  # float32 mono
        ...


class CachedTTS:
    """Wraps a backend; identical (backend, voice, text, rate) requests hit disk."""

    def __init__(self, backend: TTSBackend, cache_dir: Path):
        self.backend = backend
        self.sample_rate = backend.sample_rate
        self.dir = cache_dir / backend.name
        self.dir.mkdir(parents=True, exist_ok=True)

    def synth(self, text: str, rate: float = 1.0) -> np.ndarray:
        key = hashlib.sha256(f"{self.backend.name}\x00{text}\x00{rate:.3f}".encode()).hexdigest()
        path = self.dir / f"{key}.npy"
        if path.exists():
            return np.load(path)
        wav = self.backend.synth(text, rate).astype(np.float32)
        np.save(path, wav)
        return wav
