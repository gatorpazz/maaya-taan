"""Best-of-N synthesis: sample several VITS renderings and keep the one whose
MMS-ASR transcript is closest to the target text. Mitigates the model's
stochastic drop-outs on short Maya chunks. Slow (ASR is a 1B model): used with
`maya render --rescore`; results are cached like any other synthesis."""
from __future__ import annotations

import difflib
import re

import numpy as np
import torch


def normalize_for_cer(s: str) -> str:
    """ASR outputs colonial spelling (c, qu, z); map to INALI before comparing."""
    s = s.lower().replace("qu", "k").replace("c", "k").replace("z", "s")
    return re.sub(r"[^a-z'áéíóú]", "", s)


def cer(ref: str, hyp: str) -> float:
    r, h = normalize_for_cer(ref), normalize_for_cer(hyp)
    if not r:
        return 0.0
    sm = difflib.SequenceMatcher(None, r, h)
    err = sum(max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != "equal")
    return err / len(r)


class MayaASR:
    def __init__(self):
        from transformers import AutoProcessor, Wav2Vec2ForCTC

        self.proc = AutoProcessor.from_pretrained("facebook/mms-1b-all")
        self.model = Wav2Vec2ForCTC.from_pretrained("facebook/mms-1b-all").eval()
        self.proc.tokenizer.set_target_lang("yua")
        self.model.load_adapter("yua")

    def log_probs(self, wav: np.ndarray, sr: int = 16000) -> np.ndarray:
        inp = self.proc(wav, sampling_rate=sr, return_tensors="pt")
        with torch.no_grad():
            return torch.log_softmax(self.model(**inp).logits[0], dim=-1).numpy()

    def transcribe(self, wav: np.ndarray, sr: int = 16000) -> str:
        return self.proc.decode(self.log_probs(wav, sr).argmax(-1))


_ASR: "MayaASR | None" = None


def get_asr() -> "MayaASR":
    global _ASR
    if _ASR is None:
        _ASR = MayaASR()
    return _ASR


class RescoredMaya:
    """Wraps MMSMaya. Same interface; name differs so the cache namespace differs."""

    def __init__(self, base, n: int = 6):
        self.base = base
        self.asr = get_asr()
        self.n = n
        self.name = f"{base.name}-best{n}"
        self.sample_rate = base.sample_rate

    def synth(self, text: str, rate: float = 1.0) -> np.ndarray:
        best, best_cer, best_hyp = None, 9.0, ""
        for seed in range(self.n):
            torch.manual_seed(seed)
            wav = self.base.synth(text, rate)
            hyp = self.asr.transcribe(wav, self.sample_rate)
            c = cer(text, hyp)
            if c < best_cer:
                best, best_cer, best_hyp = wav, c, hyp
            if c == 0.0:
                break
        print(f"  rescore {text!r} -> {best_hyp!r} (cer {best_cer:.0%})")
        return best
