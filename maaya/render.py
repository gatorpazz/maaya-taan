"""Turn a Script into an MP3: synthesize each segment, insert exact silences,
level-match voices, loudness-normalize, tag."""
from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from maaya import timing
from maaya.script import Script
from maaya.align import Aligner
from maaya.tts.base import CachedTTS

TARGET_SR = 24000
GAP_AFTER_SPEECH = 0.35  # small natural gap after every utterance


@dataclass
class Voices:
    narrator: CachedTTS
    maya: CachedTTS
    aligner: "Aligner | None" = None  # enables slice_of segments


def _maya_clip(voices: Voices, seg) -> np.ndarray:
    if seg.slice_of and voices.aligner is not None:
        full = voices.maya.synth(seg.slice_of, seg.rate)
        try:
            return voices.aligner.slice(full, seg.slice_of, seg.text, voices.maya.sample_rate, key=f"{voices.maya.backend.name}:{seg.rate:.2f}")
        except ValueError as e:
            print(f"warning: {e}; synthesizing fragment directly")
    return voices.maya.synth(seg.text, seg.rate)


def _to_sr(wav: np.ndarray, sr: int) -> np.ndarray:
    if sr == TARGET_SR:
        return wav
    from math import gcd

    g = gcd(sr, TARGET_SR)
    return resample_poly(wav, TARGET_SR // g, sr // g).astype(np.float32)


def _level(wav: np.ndarray, target_rms: float = 0.08) -> np.ndarray:
    rms = float(np.sqrt(np.mean(wav**2))) if len(wav) else 0.0
    if rms < 1e-5:
        return wav
    out = wav * (target_rms / rms)
    peak = float(np.max(np.abs(out)))
    return out / peak * 0.95 if peak > 0.95 else out


def build_waveform(script: Script, voices: Voices) -> tuple[np.ndarray, list[dict]]:
    """Returns the waveform and a timeline: one dict per segment with start/end seconds."""
    parts: list[np.ndarray] = []
    timeline: list[dict] = []
    t = 0.0
    for seg in script.segments:
        if seg.kind == "pause":
            secs = seg.seconds
            if seg.relative_to:
                clip = len(voices.maya.synth(seg.relative_to, seg.rate)) / voices.maya.sample_rate
                secs = timing.response_pause(clip) if seg.relative_kind == "response" else timing.repeat_pause(clip)
            parts.append(np.zeros(int(secs * TARGET_SR), np.float32))
            timeline.append({"kind": "pause", "start": round(t, 3), "end": round(t + secs, 3), "turn": seg.relative_kind, "note": seg.note})
            t += secs
            continue
        v = voices.narrator if seg.kind == "narrator" else voices.maya
        raw = _maya_clip(voices, seg) if seg.kind == "maya" else v.synth(seg.text, seg.rate)
        if seg.kind == "maya" and not seg.slice_of and len(raw) / v.sample_rate < 0.04 * len(seg.text) / seg.rate:
            print(f"warning: suspiciously short Maya clip ({len(raw)/v.sample_rate:.2f}s) for {seg.text!r}; listen to it")
        wav = _level(_to_sr(raw, v.sample_rate))
        parts.append(wav)
        parts.append(np.zeros(int(GAP_AFTER_SPEECH * TARGET_SR), np.float32))
        dur = len(wav) / TARGET_SR
        timeline.append({"kind": seg.kind, "text": seg.text, "start": round(t, 3), "end": round(t + dur, 3), "rate": seg.rate, "note": seg.note, "slice_of": seg.slice_of})
        t += dur + GAP_AFTER_SPEECH
    return (np.concatenate(parts) if parts else np.zeros(0, np.float32)), timeline


def export_mp3(wav: np.ndarray, out: Path, *, title: str, album: str, track: int | None = None, cover: Path | None = None) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, wav, TARGET_SR)
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", tmp.name]
        if cover and cover.exists():
            cmd += ["-i", str(cover), "-map", "0:a", "-map", "1:v", "-c:v", "mjpeg", "-disposition:v", "attached_pic"]
        # constant bitrate: byte offset is proportional to time, so seeking from the transcript lands exactly
        cmd += ["-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ac", "1", "-c:a", "libmp3lame", "-b:a", "64k",
                "-metadata", f"title={title}", "-metadata", f"album={album}", "-metadata", "artist=Maaya T'aan"]
        if track is not None:
            cmd += ["-metadata", f"track={track}"]
        cmd.append(str(out))
        subprocess.run(cmd, check=True)
    Path(tmp.name).unlink(missing_ok=True)
    return out


def clip_key(text: str, rate: float, slice_of: str = "") -> str:
    return f"{text}|{rate:g}|{slice_of}"


def write_clips(script: Script, voices: Voices, clips_dir: Path) -> dict[str, str]:
    """One small MP3 per distinct Maya utterance in the script, so the app can play a
    phrase or fragment on its own instead of seeking inside the lesson. Returns
    {clip_key: relative path}. Existing files are reused."""
    import hashlib

    clips_dir.mkdir(parents=True, exist_ok=True)
    out: dict[str, str] = {}
    for seg in script.segments:
        if seg.kind != "maya":
            continue
        key = clip_key(seg.text, seg.rate, seg.slice_of)
        if key in out:
            continue
        name = hashlib.sha256(key.encode()).hexdigest()[:16] + ".mp3"
        path = clips_dir / name
        if not path.exists():
            wav = _level(_to_sr(_maya_clip(voices, seg), voices.maya.sample_rate))
            pad = np.zeros(int(0.06 * TARGET_SR), np.float32)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                sf.write(tmp.name, np.concatenate([pad, wav, pad]), TARGET_SR)
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp.name, "-c:a", "libmp3lame", "-b:a", "96k", str(path)], check=True)
            Path(tmp.name).unlink(missing_ok=True)
        out[key] = f"{clips_dir.name}/{name}"
    return out


def render(script: Script, voices: Voices, out: Path, album: str = "Maaya T'aan", track: int | None = None, cover: Path | None = None,
           meanings: dict[str, str] | None = None) -> tuple[Path, dict[str, str]]:
    """Write <out>.mp3, a sibling <stem>.json timeline, and <stem>.clips/ with isolated clips."""
    import json

    wav, timeline = build_waveform(script, voices)
    export_mp3(wav, out, title=script.title, album=album, track=track, cover=cover)
    clips = write_clips(script, voices, out.with_suffix(".clips"))
    if meanings:
        for seg in timeline:
            if seg["kind"] == "maya":
                seg["en"] = meanings.get(seg["text"].lower(), "")
    out.with_suffix(".json").write_text(json.dumps({
        "lesson_id": script.lesson_id, "title": script.title, "duration": round(len(wav) / TARGET_SR, 3),
        "audio": out.name, "segments": timeline}, ensure_ascii=False, indent=0), encoding="utf-8")
    return out, clips
