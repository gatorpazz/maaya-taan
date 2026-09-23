"""Data the app reads: per-lesson reference JSON (language-specific text under
neutral keys) and a meanings lookup for the timeline."""
from __future__ import annotations

import json
from pathlib import Path

from maaya.curriculum import Item, Lesson


def meaning_lookup(lesson: Lesson, prior: dict[str, Item], lang: str = "en") -> dict[str, str]:
    """Lower-cased Maya string -> meaning, for every string the planner can emit."""
    m: dict[str, str] = {}
    for it in list(prior.values()) + lesson.items:
        m[it.yua.lower()] = it.meaning(lang)
        for chunk, gloss in it.glosses_in(lang).items():
            m.setdefault(chunk.lower(), gloss)
        for tr in it.transforms:
            m.setdefault(tr.yua.lower(), tr.prompt(lang))
    for d in (lesson.opening, lesson.closing):
        if d:
            for line in d.lines:
                m.setdefault(line.yua.lower(), line.meaning(lang))
    return m


def _item(it: Item, lang: str) -> dict:
    return {"id": it.id, "yua": it.yua, "meaning": it.meaning(lang), "literal": it.literal_in(lang), "note": it.note_in(lang),
            "syllables": it.syllables, "glosses": it.glosses_in(lang), "cues": it.cues_in(lang),
            "transforms": [{"prompt": t.prompt(lang), "yua": t.yua} for t in it.transforms]}


def _dialogue(d, lang: str) -> dict:
    return {"id": d.id, "setting": d.setting(lang), "lines": [{"speaker": l.speaker, "yua": l.yua, "meaning": l.meaning(lang)} for l in d.lines]}


def lesson_reference(lesson: Lesson, prior: dict[str, Item], clips: dict[str, str] | None, lang: str) -> dict:
    return {
        "lang": lang,
        "clips": clips or {},
        "number": lesson.number,
        "title": lesson.title_in(lang),
        "grammar_note": lesson.grammar_note_in(lang),
        "opening": _dialogue(lesson.opening, lang),
        "closing": _dialogue(lesson.closing or lesson.opening, lang),
        "items": [_item(it, lang) for it in lesson.items],
        "review_items": [_item(it, lang) for it in prior.values()],
    }


def write_reference(lesson: Lesson, prior: dict[str, Item], out_dir: Path, clips: dict[str, str] | None, lang: str) -> Path:
    out = out_dir / f"L1-{lesson.number:02d}.{lang}.lesson.json"
    out.write_text(json.dumps(lesson_reference(lesson, prior, clips, lang), ensure_ascii=False, indent=0), encoding="utf-8")
    return out
