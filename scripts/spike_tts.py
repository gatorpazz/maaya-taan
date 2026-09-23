"""Phase 0 spike: does facebook/mms-tts-yua handle Yucatec phonology?

Picks corpus phrases that exercise glottalized consonants, long vowels, high tone
and glottalized vowels, synthesizes each at normal and slow rate, reports
tokenizer coverage (<unk>) and real-time factor. Output: out/spike/*.wav
"""
from __future__ import annotations

import csv
import re
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from transformers import AutoTokenizer, VitsModel

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data/raw/YUA_ES_communicative_contexts_corpus_v1.tsv"
OUT = ROOT / "out/spike"
OUT.mkdir(parents=True, exist_ok=True)

FEATURES = {
    "glottal_k": r"k'",
    "glottal_p": r"p'",
    "glottal_t": r"t'",
    "glottal_ch": r"ch'",
    "glottal_ts": r"ts'",
    "high_tone": r"[áéíóú][aeiou]",
    "glott_vowel": r"[aeiou]'[aeiou]",
    "long_vowel": r"(aa|ee|ii|oo|uu)",
}
CLASSICS = ["Bix a beel", "Ma'alob", "In k'aaba'e'", "Ba'ax ka wa'alik", "Ko'ox", "Ma'", "Jaaj", "Yuum bo'otik", "Dios bo'otik"]


def pick_phrases() -> list[tuple[str, str, str]]:
    rows = list(csv.DictReader(CORPUS.open(encoding="utf-8"), delimiter="\t"))
    chosen: dict[str, tuple[str, str]] = {}
    for tag, pat in FEATURES.items():
        hits = sorted((r for r in rows if re.search(pat, r["YUA"]) and 15 <= len(r["YUA"]) <= 45), key=lambda r: len(r["YUA"]))
        for r in hits[:3]:
            chosen.setdefault(r["YUA"], (tag, r["ES"]))
    for c in CLASSICS:
        hits = sorted((r for r in rows if r["YUA"].lower().startswith(c.lower())), key=lambda r: len(r["YUA"]))
        if hits:
            chosen.setdefault(hits[0]["YUA"], ("classic", hits[0]["ES"]))
        else:
            chosen.setdefault(c, ("classic-unattested", ""))
    return [(y, t, e) for y, (t, e) in chosen.items()]


def main() -> None:
    device = sys.argv[1] if len(sys.argv) > 1 else "cpu"
    tok = AutoTokenizer.from_pretrained("facebook/mms-tts-yua")
    model = VitsModel.from_pretrained("facebook/mms-tts-yua").to(device).eval()
    sr = model.config.sampling_rate
    print(f"device={device} sr={sr} vocab={len(tok)} unk_id={tok.unk_token_id}")
    phrases = pick_phrases()
    total_audio = 0.0
    total_wall = 0.0
    for i, (yua, tag, es) in enumerate(phrases):
        ids = tok(yua, return_tensors="pt")
        unk = int((ids.input_ids == tok.unk_token_id).sum())
        for rate in (1.0, 0.7):
            model.speaking_rate = rate
            t0 = time.perf_counter()
            with torch.no_grad():
                wav = model(**ids.to(device)).waveform[0].cpu().numpy()
            wall = time.perf_counter() - t0
            dur = len(wav) / sr
            total_audio += dur
            total_wall += wall
            name = f"{i:02d}_{tag}_r{int(rate*100)}.wav"
            sf.write(OUT / name, wav.astype(np.float32), sr)
        print(f"[{i:02d}] {tag:18s} unk={unk} {dur:4.1f}s  {yua}   |  {es}")
    print(f"\nRTF={total_wall/total_audio:.3f}  ({total_audio:.0f}s audio in {total_wall:.1f}s wall)")
    print(f"wrote {len(phrases)*2} files to {OUT}")


if __name__ == "__main__":
    main()
