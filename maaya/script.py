"""Timed lesson script: the audio-free intermediate between planner and renderer."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from maaya import timing

Kind = Literal["narrator", "maya", "pause"]


class Segment(BaseModel):
    kind: Kind
    text: str = ""
    rate: float = 1.0  # speaking rate for TTS segments
    slice_of: str = ""  # maya only: cut this fragment out of the rendering of the full phrase
    seconds: float = 0.0  # duration for pause segments (an estimate when relative_to is set)
    relative_to: str = ""  # pause sized at render time from this Maya text's real clip length
    relative_kind: Literal["", "response", "repeat"] = ""
    note: str = ""  # free-form, e.g. item id / stage, for debugging


class Script(BaseModel):
    lesson_id: str
    title: str
    segments: list[Segment] = Field(default_factory=list)

    # builder helpers ---------------------------------------------------
    def narrator(self, text: str, note: str = "") -> "Script":
        self.segments.append(Segment(kind="narrator", text=text, note=note))
        return self

    def maya(self, text: str, rate: float = 1.0, note: str = "", slice_of: str = "") -> "Script":
        self.segments.append(Segment(kind="maya", text=text, rate=rate, note=note, slice_of=slice_of))
        return self

    def pause(self, seconds: float, note: str = "") -> "Script":
        self.segments.append(Segment(kind="pause", seconds=seconds, note=note))
        return self

    def response_pause(self, text: str, rate: float = 1.0, note: str = "") -> "Script":
        """Anticipation gap sized from the real clip at render time; estimate now."""
        self.segments.append(Segment(kind="pause", seconds=timing.response_pause(timing.maya_seconds(text, rate)), relative_to=text, rate=rate, relative_kind="response", note=note))
        return self

    def repeat_pause(self, text: str, rate: float = 1.0, note: str = "") -> "Script":
        self.segments.append(Segment(kind="pause", seconds=timing.repeat_pause(timing.maya_seconds(text, rate)), relative_to=text, rate=rate, relative_kind="repeat", note=note))
        return self
