"""Static site build: everything the public app needs, no server.

site/
  index.html, app.js, styles.css, sw.js, guide.json, icons   (from pwa/)
  site.json          contact links and the public base path
  manifest.json      lesson list, rendered for a fresh learner in order
  lessons/           L1-NN.mp3, L1-NN.json, L1-NN.lesson.json, L1-NN.clips/
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from maaya.curriculum import Level

ROOT = Path(__file__).resolve().parents[1]
PWA = ROOT / "pwa"
LESSONS = ROOT / "out/lessons"
SITE = ROOT / "site"
SITE_CONFIG = ROOT / "site.json"

DEFAULT_CONFIG = {
    "name": "Maaya T'aan",
    "tagline": "Learn Yucatec Maya by ear. Free, Pimsleur-style audio lessons.",
    "contact_url": "",
    "contact_label": "",
    "repo_url": "",
    "recordings_url": "",
}


def load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    if SITE_CONFIG.exists():
        cfg.update(json.loads(SITE_CONFIG.read_text(encoding="utf-8")))
    return cfg


def public_manifest(level: Level) -> dict:
    rows = []
    for les in level.lessons:
        lid = f"L1-{les.number:02d}"
        tl = LESSONS / f"{lid}.json"
        if not tl.exists():
            continue
        t = json.loads(tl.read_text(encoding="utf-8"))
        rows.append({"id": lid, "number": les.number, "title": les.title, "duration": t["duration"],
                     "new_items": len(les.items), "items": [{"id": i.id, "yua": i.yua, "en": i.en} for i in les.items]})
    return {"level": level.name, "lessons": rows}


def build(level: Level, out: Path = SITE) -> Path:
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(PWA, out)
    (out / "lessons").mkdir()
    for les in public_manifest(level)["lessons"]:
        lid = les["id"]
        for suffix in (".mp3", ".json", ".lesson.json"):
            shutil.copy2(LESSONS / f"{lid}{suffix}", out / "lessons" / f"{lid}{suffix}")
        clips = LESSONS / f"{lid}.clips"
        if clips.exists():
            shutil.copytree(clips, out / "lessons" / f"{lid}.clips")
    (out / "manifest.json").write_text(json.dumps(public_manifest(level), ensure_ascii=False), encoding="utf-8")
    (out / "site.json").write_text(json.dumps(load_config(), ensure_ascii=False, indent=2), encoding="utf-8")
    (out / ".nojekyll").write_text("")
    return out
