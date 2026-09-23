"""Yucatec Maya voice: facebook/mms-tts-yua (VITS). Local, CPU is plenty fast."""
from __future__ import annotations

import numpy as np
import torch


class MMSMaya:
    name = "mms-tts-yua"

    def __init__(self, device: str = "cpu"):
        from transformers import AutoTokenizer, VitsModel

        self.tok = AutoTokenizer.from_pretrained("facebook/mms-tts-yua")
        self.model = VitsModel.from_pretrained("facebook/mms-tts-yua").to(device).eval()
        self.device = device
        self.sample_rate = self.model.config.sampling_rate

    def synth(self, text: str, rate: float = 1.0) -> np.ndarray:
        ids = self.tok(text, return_tensors="pt")
        if int((ids.input_ids == self.tok.unk_token_id).sum()):
            raise ValueError(f"mms-tts-yua cannot represent some characters in: {text!r}")
        self.model.speaking_rate = rate
        with torch.no_grad():
            wav = self.model(**ids.to(self.device)).waveform[0].cpu().numpy()
        return _trim(wav, self.sample_rate)


def _trim(wav: np.ndarray, sr: int, thresh: float = 0.01, pad: float = 0.08) -> np.ndarray:
    """Strip leading/trailing near-silence, keep a small pad so segments breathe."""
    idx = np.where(np.abs(wav) > thresh)[0]
    if len(idx) == 0:
        return wav
    p = int(pad * sr)
    return wav[max(0, idx[0] - p) : min(len(wav), idx[-1] + p)]
