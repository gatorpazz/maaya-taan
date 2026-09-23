"""`maya` command line."""
from __future__ import annotations

import json
from pathlib import Path

import typer

from maaya.curriculum import load_level

app = typer.Typer(help="Pimsleur-style Yucatec Maya lesson generator.", no_args_is_help=True)

ROOT = Path(__file__).resolve().parents[1]
CURRICULUM = ROOT / "curriculum"
OUT = ROOT / "out"
LEARNER = ROOT / "learner.json"
CACHE = ROOT / ".cache/tts"


def _level(level: str):
    return load_level(CURRICULUM / level)


STATE_PATH = [LEARNER]  # swapped to the canonical file during `maya build`


def _state():
    from maaya.learner import LearnerState

    return LearnerState.load(STATE_PATH[0])


def _plan(level: str, lesson: int, lang: str = "en"):
    from maaya.planner import plan_lesson

    lv = _level(level)
    les = next((l for l in lv.lessons if l.number == lesson), None)
    if les is None:
        raise typer.BadParameter(f"no lesson {lesson} in {level}")
    prior = {i.id: i for i in lv.items_before(lesson)}
    return plan_lesson(les, prior, _state(), lang=lang)


@app.command()
def plan(lesson: int, level: str = "level1", lang: str = "en"):
    """Write the timed script for a lesson to out/scripts/ and print its estimated length."""
    p = _plan(level, lesson, lang)
    path = OUT / "scripts" / f"{p.script.lesson_id}.{lang}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(p.script.model_dump_json(indent=1))
    n_seg = len(p.script.segments)
    typer.echo(f"{p.script.lesson_id}: ~{p.estimated_seconds/60:.1f} min, {n_seg} segments, {len(p.new_items)} new items, {len(p.reviewed)} reviews -> {path}")


@app.command()
def render(lesson: int, level: str = "level1", lang: str = "en", narrator_voice: str = "",
           rescore: bool = typer.Option(True, help="best-of-N Maya synthesis picked by MMS-ASR agreement")):
    """Plan and render a lesson to out/lessons/<id>.<lang>.mp3 (TTS results are cached)."""
    from maaya.strings import NARRATOR_VOICE

    lang_code, default_voice = NARRATOR_VOICE[lang]
    narrator_voice = narrator_voice or default_voice
    from maaya.render import Voices, render as _render
    from maaya.tts.base import CachedTTS
    from maaya.tts.kokoro import KokoroNarrator
    from maaya.tts.mms import MMSMaya

    p = _plan(level, lesson, lang)
    maya_voice = MMSMaya()
    if rescore:
        from maaya.tts.rescore import RescoredMaya

        maya_voice = RescoredMaya(maya_voice)
    from maaya.align import Aligner
    from maaya.tts.rescore import get_asr

    from maaya.export import meaning_lookup, write_reference

    voices = Voices(narrator=CachedTTS(KokoroNarrator(narrator_voice, lang_code), CACHE), maya=CachedTTS(maya_voice, CACHE), aligner=Aligner(get_asr(), CACHE))
    lv = _level(level)
    les = next(l for l in lv.lessons if l.number == lesson)
    prior = {i.id: i for i in lv.items_before(lesson)}
    out, clips = _render(p.script, voices, OUT / "lessons" / f"{p.script.lesson_id}.{lang}.mp3", album=f"Maaya T'aan {level} ({lang})", track=lesson,
                         cover=ROOT / "assets/cover.jpg", meanings=meaning_lookup(les, prior, lang), clips_dir=OUT / "lessons" / f"{p.script.lesson_id}.clips")
    write_reference(les, prior, OUT / "lessons", clips, lang)
    typer.echo(f"wrote {out} (+ .json timeline, .lesson.json reference, {len(clips)} clips)")


@app.command()
def complete(lesson: int, level: str = "level1", failed: list[str] = typer.Option([], "--failed", "-f", help="item ids you could not recall")):
    """Mark a lesson done so the next one schedules its reviews. Run after listening."""
    p = _plan(level, lesson)
    st = _state()
    st.introduce(p.new_items, lesson)
    st.complete(lesson, p.reviewed, failed=set(failed))
    st.save(STATE_PATH[0])
    typer.echo(f"lesson {lesson} completed: {len(p.new_items)} new, {len(p.reviewed)} reviewed, {len(failed)} failed")


@app.command()
def status(level: str = "level1"):
    """Show completed lessons and what's due next."""
    st = _state()
    nxt = (max(st.completed) + 1) if st.completed else 1
    typer.echo(f"completed: {st.completed or 'none'}   next: lesson {nxt}")
    lv = _level(level)
    names = {i.id: i.yua for i in lv.items_before(99)}
    for iid, stage in st.due(nxt):
        typer.echo(f"  due: {iid:22s} stage {stage}  {names.get(iid, '')}")


@app.command()
def attest(text: str):
    """Check whether a Maya string is attested in the corpus / dictionary."""
    from maaya.attest import Attester

    r = Attester().check(text)
    typer.echo(f"{r.level}: {text}")
    if r.exact_ids:
        typer.echo(f"  corpus ids: {', '.join(r.exact_ids[:5])}")
    if r.unknown_words:
        typer.echo(f"  unknown words: {', '.join(r.unknown_words)}")
    for pid, yua, es in r.similar[:5]:
        typer.echo(f"  similar {pid}: {yua}  |  {es}")


@app.command()
def lint(level: str = "level1", lang: str = "en"):
    """Validate every lesson: attestation, item counts, duplicate ids, estimated length; with --lang es, missing Spanish."""
    from maaya.attest import Attester
    from maaya.learner import LearnerState
    from maaya.planner import plan_lesson

    lv = _level(level)
    a = Attester()
    problems = 0
    seen: set[str] = set()
    for les in lv.lessons:
        strings = [(f"item {i.id}", i.yua, i.attested_by) for i in les.items]
        strings += [(f"transform of {i.id}", t.yua, t.attested_by) for i in les.items for t in i.transforms]
        for d in (les.opening, les.closing):
            if d:
                strings += [(f"dialogue {d.id} line {n+1}", l.yua, l.attested_by) for n, l in enumerate(d.lines)]
        for label, yua, claimed in strings:
            r = a.check(yua)
            if "REVIEW" in claimed:
                typer.echo(f"L{les.number:02d} REVIEW  {label}: {yua}")
                problems += 1
            elif not r.ok:
                typer.echo(f"L{les.number:02d} {r.level.upper():7s} {label}: {yua}  unknown={r.unknown_words}")
                problems += 1
        for i in les.items:
            for c in i.syllables:
                if c.lower() not in i.yua.lower():
                    typer.echo(f"L{les.number:02d} CHUNK   {i.id}: {c!r} is not part of {i.yua!r}")
                    problems += 1
            for g in list(i.glosses) + list(i.glosses_es):  # a gloss keys a buildup chunk or a word of the phrase
                if g.lstrip("-").lower() not in i.yua.lower():
                    typer.echo(f"L{les.number:02d} GLOSS   {i.id}: gloss for {g!r} is not part of {i.yua!r}")
                    problems += 1
            if i.id in seen:
                typer.echo(f"L{les.number:02d} DUP     item {i.id} already taught")
                problems += 1
            seen.add(i.id)
        if not 6 <= len(les.items) <= 12:
            typer.echo(f"L{les.number:02d} COUNT   {len(les.items)} new items (want 6-12)")
            problems += 1
        if lang == "es":
            for f in les.missing_es():
                typer.echo(f"L{les.number:02d} NO-ES   {f}")
                problems += 1
        est = plan_lesson(les, {i.id: i for i in lv.items_before(les.number)}, LearnerState(), lang=lang).estimated_seconds / 60
        if not 26 <= est <= 34:
            typer.echo(f"L{les.number:02d} LENGTH  ~{est:.1f} min (fresh learner estimate)")
            problems += 1
    typer.echo(f"{len(lv.lessons)} lessons, {problems} problems")
    raise typer.Exit(code=1 if problems else 0)


@app.command()
def draft(lesson: int, level: str = "level1", force: bool = False,
          backend: str = typer.Option("auto", help="claude (Claude Code CLI, your subscription), api (ANTHROPIC_API_KEY), or auto")):
    """Draft lessonNN.yaml with Claude from corpus-attested phrases. Review the file, then `maya lint`."""
    from maaya.draft import draft as _draft, to_yaml

    path = CURRICULUM / level / f"lesson{lesson:02d}.yaml"
    if path.exists() and not force:
        raise typer.BadParameter(f"{path} exists; pass --force to overwrite")
    lv = _level(level)
    les, needs_review, _ = _draft(lesson, lv.items_before(lesson), backend=backend)
    path.write_text(to_yaml(les), encoding="utf-8")
    flagged = [i.id for i in les.items if "REVIEW" in i.attested_by]
    typer.echo(f"wrote {path}: {len(les.items)} items, {len(flagged)} flagged REVIEW {flagged}")
    if needs_review:
        typer.echo("model wanted but could not attest: " + "; ".join(needs_review))


@app.command()
def build(level: str = "level1", upto: int = 0, rescore: bool = True, langs: str = "en,es"):
    """Render every lesson in order for a fresh learner (the public course), in each language, and build site/."""
    from maaya.learner import LearnerState
    from maaya.site import build as _build

    canonical = OUT / "canonical-learner.json"
    STATE_PATH[0] = canonical
    if canonical.exists():
        canonical.unlink()
    lv = _level(level)
    for les in lv.lessons:
        if upto and les.number > upto:
            break
        for lang in langs.split(","):
            render(les.number, level=level, lang=lang, rescore=rescore)
        p = _plan(level, les.number)
        st = LearnerState.load(canonical)
        st.introduce(p.new_items, les.number)
        st.complete(les.number, p.reviewed)
        st.save(canonical)
    out = _build(lv)
    typer.echo(f"site built at {out}; preview with: uv run maya serve")


@app.command()
def serve(host: str = "0.0.0.0", port: int = 8000):
    """Serve the built site/ locally (same files GitHub Pages would serve)."""
    import functools
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

    from maaya.site import SITE

    if not SITE.exists():
        raise typer.BadParameter("no site/ yet; run `maya build` first")

    class H(SimpleHTTPRequestHandler):
        """Static files with byte-range support (audio seeking), like a real static host."""

        protocol_version = "HTTP/1.1"

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

        def log_message(self, *a):
            pass

        def do_GET(self):
            rng = self.headers.get("Range", "")
            path = Path(self.translate_path(self.path))
            if not (rng.startswith("bytes=") and path.is_file()):
                return super().do_GET()
            size = path.stat().st_size
            a, _, b = rng[6:].partition("-")
            start = int(a) if a else max(0, size - int(b))
            end = int(b) if (b and a) else size - 1
            end = min(end, size - 1)
            self.send_response(206)
            self.send_header("Content-Type", self.guess_type(str(path)))
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(end - start + 1))
            self.end_headers()
            with path.open("rb") as f:
                f.seek(start)
                remaining = end - start + 1
                while remaining > 0:
                    chunk = f.read(min(1 << 16, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)

    typer.echo(f"serving {SITE} on http://{host}:{port}")
    ThreadingHTTPServer((host, port), functools.partial(H, directory=str(SITE))).serve_forever()


@app.command()
def deploy(project: str = "maaya-taan"):
    """Publish site/ to Cloudflare as Worker static assets (run `npx wrangler login` once first)."""
    import subprocess

    from maaya.site import SITE

    if not SITE.exists():
        raise typer.BadParameter("no site/ yet; run `maya build` first")
    r = subprocess.run(["npx", "--yes", "wrangler", "deploy", "--name", project], cwd=str(ROOT))
    raise typer.Exit(code=r.returncode)


@app.command(name="next-lesson")
def next_lesson(level: str = "level1"):
    """Print the next lesson number to write and its syllabus row."""
    import re

    lv = _level(level)
    n = (max(l.number for l in lv.lessons) + 1) if lv.lessons else 1
    text = (CURRICULUM / level / "SYLLABUS.md").read_text(encoding="utf-8")
    row = next((line for line in text.splitlines() if re.match(rf"\|\s*{n}\s*\|", line)), "(no syllabus row)")
    typer.echo(f"next: {n}")
    typer.echo(row)
    if lv.lessons:
        last = lv.lessons[-1]
        typer.echo(f"last written: {last.number} {last.title!r} with {len(last.items)} items: " + ", ".join(i.yua for i in last.items))


@app.command(name="voice-report")
def voice_report(lesson: int, level: str = "level1", worst: int = 25):
    """Rank a rendered lesson's Maya clips by how poorly the MMS recognizer agrees with them (cached per clip)."""
    import json

    import soundfile as sf
    from scipy.signal import resample_poly

    from maaya.tts.rescore import cer, get_asr

    ref_path = OUT / "lessons" / f"L1-{lesson:02d}.en.lesson.json"
    if not ref_path.exists():
        raise typer.BadParameter(f"{ref_path} not found; render the lesson first")
    clips = json.loads(ref_path.read_text(encoding="utf-8"))["clips"]
    cache_path = OUT / "lessons" / "voice-report.json"
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    asr = None
    rows = []
    for key, rel in clips.items():
        text, rate, slice_of = key.split("|")
        path = OUT / "lessons" / rel
        ck = f"{rel}:{path.stat().st_mtime_ns}"
        if ck not in cache:
            asr = asr or get_asr()
            wav, sr = sf.read(path, dtype="float32")
            if sr != 16000:
                from math import gcd

                g = gcd(sr, 16000)
                wav = resample_poly(wav, 16000 // g, sr // g)
            hyp = asr.transcribe(wav, 16000)
            cache[ck] = {"hyp": hyp, "cer": round(cer(text, hyp), 3)}
        rows.append({"text": text, "rate": float(rate), "fragment": bool(slice_of), **cache[ck]})
    cache_path.write_text(json.dumps(cache, ensure_ascii=False))
    rows.sort(key=lambda r: -r["cer"])
    typer.echo(f"{'cer':>5}  {'rate':>4}  text -> recognizer heard      ('!' = phrase of 3+ words above 40%; fragments are cut from full-phrase audio)")
    for r in rows[:worst]:
        flag = "!" if (not r["fragment"] and len(r["text"].split()) >= 3 and r["cer"] > 0.4) else " "
        kind = "frag" if r["fragment"] else "    "
        typer.echo(f"{r['cer']:5.0%}{flag} {r['rate']:4g} {kind} {r['text']!r} -> {r['hyp']!r}")
    typer.echo(f"{len(rows)} clips")


@app.command()
def feed(base_url: str = "http://localhost:8000"):
    """Write out/podcast.xml. Serve with: python -m http.server -d out 8000"""
    from maaya.feed import write_feed

    out = write_feed(OUT / "lessons", base_url, OUT / "podcast.xml")
    typer.echo(f"wrote {out}; subscribe at {base_url}/podcast.xml")


if __name__ == "__main__":
    app()
