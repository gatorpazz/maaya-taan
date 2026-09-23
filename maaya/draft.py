"""Draft a lesson YAML with Claude, constrained to corpus-attested phrases.

The model sees the syllabus slot, everything already taught, and a few hundred
attested phrases from the relevant contexts. It must build the lesson from those.
Output is validated against the Lesson schema, then every Maya string is
attested; unattested strings get attested_by: [REVIEW] so `maya lint` flags them.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from maaya.attest import Attester
from maaya.curriculum import Item, Lesson
from maaya.lexicon import connect

MODEL = "claude-opus-5"

SYSTEM = """You write Pimsleur-style audio lessons for Yucatec Maya (Maaya T'aan), for an English-speaking total beginner.

Hard rules:
1. Every Maya string you output (dialogue lines, items, buildup chunks, transforms) must be taken verbatim from the ATTESTED PHRASES list, or be a chunk of one, or a recombination whose every word appears there. Never invent Maya. If you need a phrase that is not in the list, leave it out and mention it under `needs_review` instead.
2. Use the modern INALI orthography exactly as in the list: apostrophes for glottalization (k', p', t', ch', ts', vowel'), doubled vowels for length, acute accents for high tone.
3. A lesson has 8 to 10 new items. Prefer short, high-frequency, conversationally useful phrases. Reuse items from PREVIOUSLY TAUGHT in dialogues freely, but do not re-teach them.
4. `syllables` is the backward-buildup list in speaking order, ending with the full phrase, e.g. ["beel", "a beel", "Bix a beel"]. Build from the last word backwards; chunks may be partial words for long words.
5. `note` is one short organic hint the narrator says once (a sound, a literal meaning, a pattern). No grammar tables, no linguistic jargon beyond "prefix" or "ending".
6. `cues` are 1-2 situational prompts for recall, second person, e.g. "You meet your neighbor in the morning. Ask how she is."
7. `transforms` (optional, 0-1 per item) ask the learner to change one thing (person, object) and give the attested answer.
8. Opening dialogue: 5-8 lines between A and B, natural, using new and previously taught items. Closing dialogue: a variation on the same scene.
9. `en` is natural English, not a gloss. `literal` is the word-by-word gloss when it helps.
10. `grammar_note` is one sentence, spoken once, pointing at a pattern the learner has just heard.
11. The course is also taught in Spanish. For every English teaching field give the Spanish counterpart, written for a Spanish speaker rather than translated word by word: `es` (use the corpus Spanish for attested phrases), `literal_es`, `note_es`, `cues_es`, `glosses_es`, `prompt_es`, `setting_es`, line `es`, `title_es`, `grammar_note_es`.

Output only a YAML document in a ```yaml fence, matching this shape exactly:

number: <int>
title: <string>
title_es: <string>
opening: {id: lNN_open, setting_en: <one sentence>, setting_es: ..., lines: [{speaker: A|B, yua: ..., en: ..., es: ...}, ...]}
items:
  - {id: snake_case, yua: ..., en: ..., es: ..., literal: ..., literal_es: ..., syllables: [...], glosses: {...}, glosses_es: {...}, note: ..., note_es: ..., cues: [...], cues_es: [...], transforms: [{prompt_en: ..., prompt_es: ..., yua: ...}]}
grammar_note: <string>
grammar_note_es: <string>
closing: {id: lNN_close, setting_en: ..., setting_es: ..., lines: [...]}
needs_review: [<Maya strings you wanted but could not attest>]
"""


def _syllabus_row(number: int) -> str:
    text = (Path(__file__).resolve().parents[1] / "curriculum/level1/SYLLABUS.md").read_text(encoding="utf-8")
    for line in text.splitlines():
        if re.match(rf"\|\s*{number}\s*\|", line):
            return line
    raise ValueError(f"lesson {number} not in SYLLABUS.md")


def _contexts_from_row(row: str) -> list[str]:
    return [f"COMMC{c}" for c in re.findall(r"\b(\d{4})\b", row.split("|")[-2])]


def corpus_sample(context_ids: list[str], limit_per_ctx: int = 150, max_len: int = 60) -> list[tuple[str, str, str]]:
    """Shortest phrases first: they are the most reusable in a beginner lesson."""
    con = connect()
    out = []
    for cid in context_ids:
        rows = con.execute(
            "SELECT id, yua, es FROM phrases WHERE context=? AND length(yua)<=? ORDER BY length(yua), id LIMIT ?", (cid, max_len, limit_per_ctx)
        ).fetchall()
        out += [(r["id"], r["yua"], r["es"]) for r in rows]
    return out


def build_prompt(number: int, taught: list[Item]) -> str:
    row = _syllabus_row(number)
    sample = corpus_sample(_contexts_from_row(row) or ["COMMC0019"])
    taught_txt = "\n".join(f"- {i.id}: {i.yua} = {i.en}" for i in taught) or "- (nothing yet)"
    phrases_txt = "\n".join(f"{pid}\t{yua}\t{es}" for pid, yua, es in sample)
    return f"""SYLLABUS SLOT (markdown table row: number | title | new material | grammar seed | contexts):
{row}

PREVIOUSLY TAUGHT (do not re-teach; reuse freely):
{taught_txt}

ATTESTED PHRASES (id, Maya, Spanish) — the only Maya you may use:
{phrases_txt}

Write lesson {number}."""


def draft(number: int, taught: list[Item]) -> tuple[Lesson, list[str], str]:
    """Returns (validated lesson with attestation filled in, needs_review list, raw yaml)."""
    import anthropic

    client = anthropic.Anthropic()
    with client.messages.stream(
        model=MODEL,
        max_tokens=32000,
        output_config={"effort": "high"},
        system=SYSTEM,
        messages=[{"role": "user", "content": build_prompt(number, taught)}],
    ) as stream:
        msg = stream.get_final_message()
    if msg.stop_reason == "refusal":
        raise RuntimeError(f"model refused: {msg.stop_details}")
    text = "".join(b.text for b in msg.content if b.type == "text")
    m = re.search(r"```yaml\s*(.*?)```", text, re.S)
    raw = m.group(1) if m else text
    data = yaml.safe_load(raw)
    needs_review = data.pop("needs_review", []) or []
    lesson = Lesson.model_validate(data)
    _fill_attestation(lesson)
    return lesson, needs_review, raw


def _fill_attestation(lesson: Lesson) -> None:
    a = Attester()

    def ids(text: str) -> list[str]:
        r = a.check(text)
        return r.exact_ids[:3] if r.level == "exact" else (["words"] if r.level == "words" else ["REVIEW"])

    for d in (lesson.opening, lesson.closing):
        if d:
            for line in d.lines:
                line.attested_by = ids(line.yua)
    for it in lesson.items:
        it.attested_by = ids(it.yua)
        for t in it.transforms:
            t.attested_by = ids(t.yua)


def to_yaml(lesson: Lesson) -> str:
    return yaml.safe_dump(lesson.model_dump(exclude_defaults=True), allow_unicode=True, sort_keys=False, width=120)
