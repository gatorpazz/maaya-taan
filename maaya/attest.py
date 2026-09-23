"""Attestation guardrail: is this Maya string backed by a human-authored source?

Levels, strongest first:
  exact   - the whole phrase is a corpus phrase (case/punctuation-insensitive)
  words   - every word occurs in the corpus or Wiktionary; phrase itself is novel
  partial - some words unknown
  none    - nothing recognised
"""
from __future__ import annotations

import difflib
import sqlite3
from dataclasses import dataclass, field

from maaya.lexicon import connect, normalize, tokens


@dataclass
class Attestation:
    text: str
    level: str  # exact | words | partial | none
    exact_ids: list[str] = field(default_factory=list)
    unknown_words: list[str] = field(default_factory=list)
    similar: list[tuple[str, str, str]] = field(default_factory=list)  # (id, yua, es)

    @property
    def ok(self) -> bool:
        return self.level in ("exact", "words")


class Attester:
    def __init__(self, con: sqlite3.Connection | None = None):
        self.con = con or connect()

    def word_known(self, w: str) -> bool:
        if self.con.execute("SELECT 1 FROM words WHERE word_norm=?", (w,)).fetchone():
            return True
        return bool(self.con.execute("SELECT 1 FROM lemmas WHERE word_norm=?", (w,)).fetchone())

    def similar(self, text: str, k: int = 5) -> list[tuple[str, str, str]]:
        toks = tokens(text)
        if not toks:
            return []
        # candidates: phrases sharing any token, ranked by difflib ratio
        q = " OR ".join(f'"{t}"' for t in toks)
        rows = self.con.execute(
            "SELECT p.id, p.yua, p.es FROM phrases_fts f JOIN phrases p ON p.id=f.id WHERE phrases_fts MATCH ? LIMIT 400", (q,)
        ).fetchall()
        norm = normalize(text)
        scored = sorted(rows, key=lambda r: -difflib.SequenceMatcher(None, norm, normalize(r["yua"])).ratio())
        return [(r["id"], r["yua"], r["es"]) for r in scored[:k]]

    def check(self, text: str) -> Attestation:
        norm = normalize(text)
        ids = [r["id"] for r in self.con.execute("SELECT id FROM phrases WHERE yua_norm=?", (norm,))]
        if ids:
            return Attestation(text, "exact", exact_ids=ids)
        toks = tokens(text)
        unknown = [t for t in toks if not self.word_known(t)]
        level = "words" if not unknown else ("partial" if len(unknown) < len(toks) else "none")
        return Attestation(text, level, unknown_words=unknown, similar=self.similar(text))
