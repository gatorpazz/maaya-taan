"""Slice a fragment (syllable, word, tail of a phrase) out of the full-phrase
rendering, using CTC forced alignment with the MMS Maya recognizer.

Why: mms-tts-yua says whole phrases well but garbles isolated fragments, and
Pimsleur builds every new phrase up sound by sound. So we render the whole
phrase and cut it, instead of synthesizing "lob" on its own."""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

FRAME = 320  # wav2vec2 stride at 16 kHz = 20 ms


def ctc_viterbi(logp: np.ndarray, tokens: list[int], blank: int = 0) -> list[tuple[int, int]]:
    """Best monotonic alignment of `tokens` to frames. Returns (start, end) frame per token."""
    T = logp.shape[0]
    ext = [blank]
    for t in tokens:
        ext += [t, blank]
    S = len(ext)
    NEG = -1e30
    dp = np.full((T, S), NEG)
    bp = np.zeros((T, S), dtype=np.int32)
    dp[0, 0] = logp[0, blank]
    if S > 1:
        dp[0, 1] = logp[0, ext[1]]
    ext_arr = np.array(ext)
    skip_ok = np.zeros(S, dtype=bool)  # can come from s-2 (non-blank, differs from previous label)
    for s in range(2, S):
        skip_ok[s] = ext[s] != blank and ext[s] != ext[s - 2]
    for t in range(1, T):
        stay = dp[t - 1]
        prev1 = np.concatenate(([NEG], dp[t - 1, :-1]))
        prev2 = np.concatenate(([NEG, NEG], dp[t - 1, :-2]))
        prev2 = np.where(skip_ok, prev2, NEG)
        stack = np.stack([stay, prev1, prev2])
        best = stack.argmax(0)
        dp[t] = stack[best, np.arange(S)] + logp[t, ext_arr]
        bp[t] = np.arange(S) - best
    s = S - 1 if dp[T - 1, S - 1] >= dp[T - 1, S - 2] else S - 2
    path = np.zeros(T, dtype=np.int32)
    for t in range(T - 1, -1, -1):
        path[t] = s
        s = bp[t, s]
    spans: list[tuple[int, int]] = []
    for i in range(len(tokens)):
        s_i = 2 * i + 1
        frames = np.where(path == s_i)[0]
        if len(frames) == 0:  # degenerate; borrow neighbour
            prev_end = spans[-1][1] if spans else 0
            spans.append((prev_end, prev_end + 1))
        else:
            spans.append((int(frames[0]), int(frames[-1]) + 1))
    return spans


class Aligner:
    def __init__(self, asr, cache_dir: Path):
        self.asr = asr
        self.vocab = asr.proc.tokenizer.get_vocab()
        self.dir = cache_dir / "slices"
        self.dir.mkdir(parents=True, exist_ok=True)

    def _encode(self, text: str) -> tuple[list[int], list[int]]:
        """Token ids for alignable chars, and the original char index of each."""
        ids, pos = [], []
        for i, ch in enumerate(text.lower()):
            key = "|" if ch == " " else ch
            if key in self.vocab and key not in ("<pad>", "<s>", "</s>", "<unk>"):
                ids.append(self.vocab[key])
                pos.append(i)
        return ids, pos

    def slice(self, full_wav: np.ndarray, full_text: str, fragment: str, sr: int = 16000, key: str = "") -> np.ndarray:
        cache = self.dir / (hashlib.sha256(f"{key}\x00{full_text}\x00{fragment}".encode()).hexdigest() + ".npy")
        if cache.exists():
            return np.load(cache)
        lo = full_text.lower().rfind(fragment.lower())
        if lo < 0:
            raise ValueError(f"{fragment!r} is not a substring of {full_text!r}")
        hi = lo + len(fragment) - 1
        ids, pos = self._encode(full_text)
        logp = self.asr.log_probs(full_wav, sr)
        spans = ctc_viterbi(logp, ids, blank=self.vocab["<pad>"])
        first = next(i for i, p in enumerate(pos) if p >= lo)
        last = max(i for i, p in enumerate(pos) if p <= hi)
        start = max(0, spans[first][0] * FRAME - int(0.03 * sr))
        end = min(len(full_wav), spans[last][1] * FRAME + int(0.05 * sr))
        out = full_wav[start:end].copy()
        fade = min(int(0.008 * sr), len(out) // 4)
        if fade > 0:
            out[:fade] *= np.linspace(0, 1, fade, dtype=np.float32)
            out[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)
        np.save(cache, out)
        return out
