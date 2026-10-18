"""Attestation guardrail: is this Maya string backed by a human-authored source?

Levels, strongest first:
  exact    - the whole phrase is a corpus phrase (case/punctuation-insensitive)
  standard - the whole phrase is in data/standard_phrases.tsv: a published, sourced
             phrase from teaching materials that the corpus happens to lack
  words    - every word occurs in the corpus, the standard list, or Wiktionary; phrase itself is novel
  partial  - some words unknown
  none     - nothing recognised
"""
from __future__ import annotations

import csv
import difflib
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from maaya.lexicon import connect, normalize, tokens

STANDARD_PATH = Path(__file__).resolve().parents[1] / "data" / "standard_phrases.tsv"


@dataclass
class StandardPhrase:
    id: str
    yua: str
    es: str
    en: str
    sources: str  # comma-separated keys into data/SOURCES.md
    note: str


def load_standard(path: Path = STANDARD_PATH) -> list[StandardPhrase]:
    """Hand-curated phrases from published teaching materials (see data/SOURCES.md)."""
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [StandardPhrase(r["id"], r["yua"].strip(), r["es"].strip(), r["en"].strip(), r["sources"].strip(), r.get("note", "").strip())
                for r in csv.DictReader(f, delimiter="\t") if r.get("yua", "").strip() and not r["id"].startswith("#")]


@dataclass
class Attestation:
    text: str
    level: str  # exact | standard | words | partial | none
    exact_ids: list[str] = field(default_factory=list)
    standard: list[StandardPhrase] = field(default_factory=list)
    unknown_words: list[str] = field(default_factory=list)
    similar: list[tuple[str, str, str]] = field(default_factory=list)  # (id, yua, es)

    @property
    def ok(self) -> bool:
        return self.level in ("exact", "standard", "words")

    @property
    def ids(self) -> list[str]:
        return self.exact_ids or [sp.id for sp in self.standard]


class Attester:
    def __init__(self, con: sqlite3.Connection | None = None, standard: list[StandardPhrase] | None = None):
        self.con = con or connect()
        self.standard = load_standard() if standard is None else standard
        self._standard_by_norm: dict[str, list[StandardPhrase]] = {}
        self._standard_words: set[str] = set()
        for sp in self.standard:
            self._standard_by_norm.setdefault(normalize(sp.yua), []).append(sp)
            self._standard_words.update(tokens(sp.yua))

    def word_known(self, w: str) -> bool:
        if w in self._standard_words:
            return True
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
        std = self._standard_by_norm.get(norm)
        if std:
            return Attestation(text, "standard", standard=std)
        toks = tokens(text)
        unknown = [t for t in toks if not self.word_known(t)]
        level = "words" if not unknown else ("partial" if len(unknown) < len(toks) else "none")
        return Attestation(text, level, unknown_words=unknown, similar=self.similar(text))
