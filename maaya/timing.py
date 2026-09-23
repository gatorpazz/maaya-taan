"""Duration model, calibrated on rendered lesson 1 (2026-09-22) against the
TTS cache: Kokoro af_heart and mms-tts-yua. Pause sizes follow Pimsleur:
generous room to think and answer out loud."""
from __future__ import annotations

GAP = 0.35  # silence appended after every utterance by the renderer
AFTER_ANSWER = 1.2  # breath before the narrator moves on


NARRATOR_SPC = {"en": (0.0564, 0.57), "es": (0.0564, 0.44)}  # (seconds per char, intercept); es recalibrated below


def narrator_seconds(text: str, lang: str = "en") -> float:
    a, b = NARRATOR_SPC.get(lang, NARRATOR_SPC["en"])
    return max(0.8, a * len(text) + b)


def maya_seconds(text: str, rate: float = 1.0) -> float:
    return max(0.5, (0.060 * len(text) + 0.06) * rate ** -0.65)


def response_pause(clip_seconds: float) -> float:
    """Room to recall and say the phrase: think time plus 2.5x the clip."""
    return max(3.5, 2.0 + 2.5 * clip_seconds)


def repeat_pause(clip_seconds: float) -> float:
    """Room to repeat something just heard."""
    return max(2.5, 1.2 + 2.0 * clip_seconds)
