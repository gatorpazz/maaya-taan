"""Curriculum schema. YAML files under curriculum/<level>/lessonNN.yaml are the
source of truth; Claude may draft them, a human edits them, `maya lint` checks them."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, model_validator

ItemType = Literal["word", "phrase", "construction"]


class Item(BaseModel):
    id: str  # snake_case, stable across lessons, e.g. bix_a_beel
    yua: str
    en: str
    es: str = ""
    type: ItemType = "phrase"
    syllables: list[str] = Field(default_factory=list)
    """Backward-buildup chunks in *speaking* order, e.g. ["beel", "a beel", "Bix a beel"].
    Empty means: no buildup (single short word)."""
    literal: str = ""  # literal gloss, e.g. "how (is) your road"
    glosses: dict[str, str] = Field(default_factory=dict)
    """Meaning of a buildup chunk, spoken before it: {"beel": "road", "a beel": "your road"}."""
    note: str = ""  # one organic teaching hint spoken by the narrator, optional
    cues: list[str] = Field(default_factory=list)
    """Situational prompts for stage-3 recall, e.g. "You meet your neighbor. Ask how she is." """
    attested_by: list[str] = Field(default_factory=list)  # corpus phrase ids, or ["REVIEW"]
    transforms: list["Transform"] = Field(default_factory=list)


class Transform(BaseModel):
    """Stage-4 recall: 'now say *he* is going'. Answer must itself be attested."""
    prompt_en: str
    yua: str
    attested_by: list[str] = Field(default_factory=list)


class Line(BaseModel):
    speaker: Literal["A", "B"]
    yua: str
    en: str
    attested_by: list[str] = Field(default_factory=list)


class Dialogue(BaseModel):
    id: str
    setting_en: str  # narrator's one-sentence scene description
    lines: list[Line]


class Lesson(BaseModel):
    number: int
    title: str
    opening: Dialogue
    items: list[Item]  # new items, in teaching order (8–12)
    grammar_note: str = ""  # one sentence, spoken once, organic not formal
    closing: Dialogue | None = None  # defaults to opening if omitted

    @model_validator(mode="after")
    def _check(self) -> "Lesson":
        ids = [i.id for i in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError(f"duplicate item ids in lesson {self.number}")
        return self


class Level(BaseModel):
    name: str
    lessons: list[Lesson]

    def items_before(self, lesson_number: int) -> list[Item]:
        return [i for l in self.lessons if l.number < lesson_number for i in l.items]


def load_lesson(path: Path) -> Lesson:
    return Lesson.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def load_level(folder: Path) -> Level:
    lessons = sorted((load_lesson(p) for p in folder.glob("lesson*.yaml")), key=lambda l: l.number)
    return Level(name=folder.name, lessons=lessons)
