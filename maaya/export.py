"""Data the PWA reads: per-lesson reference JSON and a meanings lookup for the timeline."""
from __future__ import annotations

import json
from pathlib import Path

from maaya.curriculum import Item, Lesson, Level


def meaning_lookup(lesson: Lesson, prior: dict[str, Item]) -> dict[str, str]:
    """Lower-cased Maya string -> English, for every string the planner can emit."""
    m: dict[str, str] = {}
    for it in list(prior.values()) + lesson.items:
        m[it.yua.lower()] = it.en
        for chunk, gloss in it.glosses.items():
            m.setdefault(chunk.lower(), gloss)
        for tr in it.transforms:
            m.setdefault(tr.yua.lower(), tr.prompt_en)
    for d in (lesson.opening, lesson.closing):
        if d:
            for line in d.lines:
                m.setdefault(line.yua.lower(), line.en)
    return m


def lesson_reference(lesson: Lesson, prior: dict[str, Item], clips: dict[str, str] | None = None) -> dict:
    return {
        "clips": clips or {},
        "number": lesson.number,
        "title": lesson.title,
        "grammar_note": lesson.grammar_note,
        "opening": lesson.opening.model_dump(),
        "closing": (lesson.closing or lesson.opening).model_dump(),
        "items": [it.model_dump() for it in lesson.items],
        "review_items": [it.model_dump() for it in prior.values()],
    }


def write_reference(lesson: Lesson, prior: dict[str, Item], out_dir: Path, clips: dict[str, str] | None = None) -> Path:
    out = out_dir / f"L1-{lesson.number:02d}.lesson.json"
    out.write_text(json.dumps(lesson_reference(lesson, prior, clips), ensure_ascii=False, indent=0), encoding="utf-8")
    return out
