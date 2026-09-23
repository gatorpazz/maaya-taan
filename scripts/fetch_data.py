"""Download the source data into data/raw/ (not committed; see data/SOURCES.md for licenses)."""
import urllib.request
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data/raw"
FILES = {
    "YUA_ES_communicative_contexts_corpus_v1.tsv": "https://raw.githubusercontent.com/alemol/yua-es-ccc/main/YUA_ES_communicative_contexts_corpus_v1.tsv",
    "contexts.tsv": "https://raw.githubusercontent.com/alemol/yua-es-ccc/main/contexts.tsv",
    "kaikki-yua.jsonl": "https://kaikki.org/dictionary/Yucatec%20Maya/kaikki.org-dictionary-YucatecMaya.jsonl",
    "inali_norma_maya.pdf": "https://site.inali.gob.mx/pdf/norma_maya.pdf",
}

if __name__ == "__main__":
    RAW.mkdir(parents=True, exist_ok=True)
    for name, url in FILES.items():
        dest = RAW / name
        if dest.exists():
            print(f"have {name}")
            continue
        print(f"fetch {name}")
        urllib.request.urlretrieve(url, dest)
    print("done; next: uv run python scripts/build_lexicon.py")
