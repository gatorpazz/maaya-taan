"""English narrator: Kokoro-82M, local, Apache-2.0."""
from __future__ import annotations

import numpy as np


class KokoroNarrator:
    name = "kokoro"
    sample_rate = 24000

    def __init__(self, voice: str = "af_heart"):
        from kokoro import KPipeline

        self.pipe = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
        self.voice = voice
        self.name = f"kokoro-{voice}"

    def synth(self, text: str, rate: float = 1.0) -> np.ndarray:
        chunks = [a for _, _, a in self.pipe(text, voice=self.voice, speed=rate)]
        wav = np.concatenate([np.asarray(c, dtype=np.float32) for c in chunks]) if chunks else np.zeros(0, np.float32)
        return wav
