"""Curriculum schema. YAML files under curriculum/<level>/lessonNN.yaml are the
source of truth; Claude may draft them, a human edits them, `maya lint` checks them."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, model_validator

ItemType = Literal["word", "phrase", "construction"]


def _pick(lang: str, en: object, es: object) -> object:
    """Spanish when asked for and present, else English."""
    return es if lang == "es" and es else en


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
    literal_es: str = ""
    glosses: dict[str, str] = Field(default_factory=dict)
    """Meaning of a buildup chunk, spoken before it: {"beel": "road", "a beel": "your road"}."""
    glosses_es: dict[str, str] = Field(default_factory=dict)
    note: str = ""  # one organic teaching hint spoken by the narrator, optional
    note_es: str = ""
    cues: list[str] = Field(default_factory=list)
    """Situational prompts for stage-3 recall, e.g. "You meet your neighbor. Ask how she is." """
    cues_es: list[str] = Field(default_factory=list)
    attested_by: list[str] = Field(default_factory=list)  # corpus phrase ids, or ["REVIEW"]
    transforms: list["Transform"] = Field(default_factory=list)

    # language accessors -----------------------------------------------
    def meaning(self, lang: str = "en") -> str:
        return str(_pick(lang, self.en, self.es))

    def literal_in(self, lang: str = "en") -> str:
        return str(_pick(lang, self.literal, self.literal_es))

    def note_in(self, lang: str = "en") -> str:
        return str(_pick(lang, self.note, self.note_es))

    def cues_in(self, lang: str = "en") -> list[str]:
        return list(_pick(lang, self.cues, self.cues_es))  # type: ignore[arg-type]

    def glosses_in(self, lang: str = "en") -> dict[str, str]:
        return dict(_pick(lang, self.glosses, self.glosses_es))  # type: ignore[arg-type]


class Transform(BaseModel):
    """Stage-4 recall: 'now say *he* is going'. Answer must itself be attested."""
    prompt_en: str
    prompt_es: str = ""
    yua: str
    attested_by: list[str] = Field(default_factory=list)

    def prompt(self, lang: str = "en") -> str:
        return str(_pick(lang, self.prompt_en, self.prompt_es))


class Line(BaseModel):
    speaker: Literal["A", "B"]
    yua: str
    en: str
    es: str = ""
    attested_by: list[str] = Field(default_factory=list)

    def meaning(self, lang: str = "en") -> str:
        return str(_pick(lang, self.en, self.es))


class Dialogue(BaseModel):
    id: str
    setting_en: str  # narrator's one-sentence scene description
    setting_es: str = ""
    lines: list[Line]

    def setting(self, lang: str = "en") -> str:
        return str(_pick(lang, self.setting_en, self.setting_es))


class Lesson(BaseModel):
    number: int
    title: str
    title_es: str = ""
    opening: Dialogue
    items: list[Item]  # new items, in teaching order (8–12)
    grammar_note: str = ""  # one sentence, spoken once, organic not formal
    grammar_note_es: str = ""
    closing: Dialogue | None = None  # defaults to opening if omitted

    def title_in(self, lang: str = "en") -> str:
        return str(_pick(lang, self.title, self.title_es))

    def grammar_note_in(self, lang: str = "en") -> str:
        return str(_pick(lang, self.grammar_note, self.grammar_note_es))

    def missing_es(self) -> list[str]:
        """Fields with no Spanish yet (for `maya lint --lang es`)."""
        out = []
        if not self.title_es: out.append("title_es")
        if self.grammar_note and not self.grammar_note_es: out.append("grammar_note_es")
        for d in (self.opening, self.closing):
            if d:
                if not d.setting_es: out.append(f"{d.id}.setting_es")
                out += [f"{d.id}.line{i+1}.es" for i, l in enumerate(d.lines) if not l.es]
        for it in self.items:
            if not it.es: out.append(f"{it.id}.es")
            if it.literal and not it.literal_es: out.append(f"{it.id}.literal_es")
            if it.note and not it.note_es: out.append(f"{it.id}.note_es")
            if it.cues and not it.cues_es: out.append(f"{it.id}.cues_es")
            if it.glosses and not it.glosses_es: out.append(f"{it.id}.glosses_es")
            out += [f"{it.id}.transform{k+1}.prompt_es" for k, t in enumerate(it.transforms) if not t.prompt_es]
        return out

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
