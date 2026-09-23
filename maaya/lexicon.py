"""SQLite lexicon of attested Yucatec Maya: corpus phrases (YUA-ES-CCC) and
Wiktionary lemmas (Kaikki). Built once by scripts/build_lexicon.py."""
from __future__ import annotations

import re
import sqlite3
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "lexicon.db"

_PUNCT = re.compile(r"[^\w' ]+", re.UNICODE)


def normalize(text: str) -> str:
    """Canonical comparison form: NFC, straight apostrophes, lowercase,
    punctuation stripped (apostrophe kept: it is a phoneme), whitespace collapsed."""
    t = unicodedata.normalize("NFC", text)
    t = t.replace("’", "'").replace("‘", "'").replace("ʼ", "'").replace("`", "'")
    t = t.lower()
    t = _PUNCT.sub(" ", t)
    return re.sub(r"\s+", " ", t).strip()


def tokens(text: str) -> list[str]:
    return [w for w in normalize(text).split(" ") if w and w != "'"]


SCHEMA = """
CREATE TABLE IF NOT EXISTS phrases (
  id TEXT PRIMARY KEY, yua TEXT NOT NULL, yua_norm TEXT NOT NULL,
  es TEXT NOT NULL, en TEXT, context TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS phrases_norm ON phrases(yua_norm);
CREATE TABLE IF NOT EXISTS contexts (id TEXT PRIMARY KEY, label TEXT NOT NULL, n INTEGER);
CREATE VIRTUAL TABLE IF NOT EXISTS phrases_fts USING fts5(id UNINDEXED, yua_norm, es, tokenize='unicode61 tokenchars ''''');
CREATE TABLE IF NOT EXISTS lemmas (
  word TEXT NOT NULL, word_norm TEXT NOT NULL, pos TEXT, gloss TEXT, tags TEXT, source TEXT
);
CREATE INDEX IF NOT EXISTS lemmas_norm ON lemmas(word_norm);
CREATE TABLE IF NOT EXISTS words (word_norm TEXT PRIMARY KEY, freq INTEGER NOT NULL);
"""


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con
