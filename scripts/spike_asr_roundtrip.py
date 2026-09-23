"""Round-trip check: MMS-TTS-yua output -> MMS-ASR (yua adapter) -> text.
If apostrophes and accents survive, the TTS is producing the contrasts."""
import re
from pathlib import Path
import soundfile as sf
import torch
from transformers import AutoProcessor, Wav2Vec2ForCTC

ROOT = Path(__file__).resolve().parents[1]
SPIKE = ROOT / "out/spike"
proc = AutoProcessor.from_pretrained("facebook/mms-1b-all")
model = Wav2Vec2ForCTC.from_pretrained("facebook/mms-1b-all").eval()
proc.tokenizer.set_target_lang("yua")
model.load_adapter("yua")

# recover originals from the spike log order
import csv, sys
sys.path.insert(0, str(ROOT / "scripts"))
from spike_tts import pick_phrases
phrases = pick_phrases()
hits = 0
for i, (yua, tag, _) in enumerate(phrases):
    wav, sr = sf.read(SPIKE / f"{i:02d}_{tag}_r100.wav")
    inputs = proc(wav, sampling_rate=sr, return_tensors="pt")
    with torch.no_grad():
        logits = model(**inputs).logits
    hyp = proc.decode(logits.argmax(-1)[0])
    norm = lambda s: re.sub(r"[^a-z'áéíóúñ ]", "", s.lower()).strip()
    ok = norm(hyp) == norm(yua)
    hits += ok
    print(f"{'OK ' if ok else 'DIFF'} | {yua:32s} | {hyp}")
print(f"\nexact matches: {hits}/{len(phrases)}")
