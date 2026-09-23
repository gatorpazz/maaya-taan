"""Build lexicon.db from data/raw/*. Idempotent (rebuilds from scratch)."""
import csv
import json
from collections import Counter
from pathlib import Path

from maaya.lexicon import DB_PATH, connect, normalize, tokens

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"


def main() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    con = connect()
    with (RAW / "contexts.tsv").open(encoding="utf-8") as f:
        con.executemany("INSERT INTO contexts VALUES (?,?,?)",
                        [(r["Context_ID"], r["Communicative_Context"], int(r["n_phrases"])) for r in csv.DictReader(f, delimiter="\t")])
    freq: Counter[str] = Counter()
    rows = []
    with (RAW / "YUA_ES_communicative_contexts_corpus_v1.tsv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            yn = normalize(r["YUA"])
            freq.update(tokens(r["YUA"]))
            rows.append((r["Phrase_ID"], r["YUA"].strip(), yn, r["ES"].strip(), None, r["Communicative_Context"]))
    con.executemany("INSERT INTO phrases VALUES (?,?,?,?,?,?)", rows)
    con.executemany("INSERT INTO phrases_fts (id, yua_norm, es) VALUES (?,?,?)", [(r[0], r[2], r[3]) for r in rows])
    con.executemany("INSERT INTO words VALUES (?,?)", freq.items())
    lemmas = []
    with (RAW / "kaikki-yua.jsonl").open(encoding="utf-8") as f:
        for line in f:
            e = json.loads(line)
            glosses = "; ".join(g for s in e.get("senses", []) for g in s.get("glosses", []))
            tags = ",".join(sorted({t for s in e.get("senses", []) for t in s.get("tags", [])}))
            lemmas.append((e["word"], normalize(e["word"]), e.get("pos"), glosses, tags, "kaikki"))
            for form in e.get("forms", []):
                if form.get("form"):
                    lemmas.append((form["form"], normalize(form["form"]), e.get("pos"), f"form of {e['word']}: {glosses}", ",".join(form.get("tags", [])), "kaikki-form"))
    con.executemany("INSERT INTO lemmas VALUES (?,?,?,?,?,?)", lemmas)
    con.commit()
    n = con.execute("SELECT count(*) FROM phrases").fetchone()[0]
    print(f"phrases={n} words={len(freq)} lemmas={len(lemmas)} -> {DB_PATH}")


if __name__ == "__main__":
    main()
