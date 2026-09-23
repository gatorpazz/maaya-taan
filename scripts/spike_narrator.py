"""Phase 0 spike: Kokoro English narrator smoke test."""
import time
from pathlib import Path
import soundfile as sf
from kokoro import KPipeline

OUT = Path(__file__).resolve().parents[1] / "out/spike"
OUT.mkdir(parents=True, exist_ok=True)
pipe = KPipeline(lang_code="a")  # American English
lines = [
    "Listen to this conversation between two friends meeting in the morning.",
    "How do you say, how are you?",
    "The word for good is pronounced from the end. Listen and repeat.",
]
t0 = time.perf_counter()
for i, text in enumerate(lines):
    for _, _, audio in pipe(text, voice="af_heart"):
        sf.write(OUT / f"narr_{i}.wav", audio, 24000)
        print(f"narr_{i}: {len(audio)/24000:.1f}s  {text}")
print(f"wall {time.perf_counter()-t0:.1f}s")
