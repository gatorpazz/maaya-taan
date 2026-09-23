# Maaya T'aan audio course

Pimsleur-style MP3 lessons for Yucatec Maya (Maaya T'aan), generated locally on a Mac.
Graduated interval recall, anticipation prompts, backward buildup, ~30 minutes per lesson.

## How it works

```
curriculum/level1/lessonNN.yaml   human-edited lessons (Claude drafts, you review)
        │   every Maya string must be attested in data/ (YUA-ES-CCC corpus, Wiktionary)
        ▼
maya plan N      → out/scripts/L1-NN.json   timed script (narrator / maya / pause)
maya render N    → out/lessons/L1-NN.mp3    Kokoro narrator + MMS Maya voice, cached TTS
maya complete N  → learner.json             schedules reviews into later lessons
maya feed        → out/podcast.xml          subscribe from a phone podcast app
```

## Setup

```bash
uv sync                         # Python deps (torch, transformers, kokoro, ...)
brew install ffmpeg espeak-ng   # audio assembly; Kokoro fallback G2P
uv run python scripts/fetch_data.py      # corpus, dictionary, orthography PDF -> data/raw/
uv run python scripts/build_lexicon.py   # builds lexicon.db from data/raw
```

Models download on first use: `facebook/mms-tts-yua` (Maya voice, CC-BY-NC), `hexgrad/Kokoro-82M` (narrator), and optionally `facebook/mms-1b-all` (Maya ASR, ~4 GB, only for the pronunciation checks in `scripts/`).

## The app (public, static)

The phone app in `pwa/` is a static site: no server, progress stays on each device. Real Pimsleur audio is fixed
too, so lessons are rendered once for a learner who goes in order; the app's own review drill (English prompt,
say it, check, hear the clip) adapts to what each person marks as missed.

```bash
uv run maya build --upto 5    # render lessons 1..5 in order with canonical progress, then assemble site/
uv run maya serve             # preview site/ at http://<this-mac>.local:8000 (phone on the same Wi-Fi)
uv run maya deploy            # publish site/ to Cloudflare Pages (npx wrangler login once first)
```

`site.json` holds the public name, tagline, and where people should send recordings or questions
(`contact_url`, `recordings_url`, `repo_url`). The About page carries the source attributions the licenses
require; keep it if you fork this.

Hosting: Cloudflare Worker static assets (`wrangler.jsonc`). `worker.js` adds HTTP byte-range support for audio, which
Cloudflare's asset serving lacks and iOS Safari requires for playback. A lesson is about 14 MB (64 kbps mono),
under the 25 MB per-file cap; 30 lessons is ~420 MB. Live: https://maaya-taan.gatorpazz.workers.dev Over https the service worker caches the app shell and
lesson data, so opened lessons keep working offline; audio streams by byte range.

## Author loop (your own adaptive lessons)

```bash
uv run maya status              # what's next, what's due
uv run maya render 3            # plan + render lesson 3 with reviews from your learner.json
uv run maya complete 3          # after listening; add --failed item_id for anything you blanked on
uv run maya feed --base-url http://<your-mac>:8000 && python -m http.server -d out 8000
```

## Two teaching languages

The course is taught in English or Spanish; the Maya is identical. Each lesson renders once per language
(`L1-01.en.mp3`, `L1-01.es.mp3`) sharing the same Maya clips; the narrator copy lives in `maaya/strings.py`
and the Spanish teaching fields sit next to the English ones in the lesson YAML (`es`, `note_es`, `cues_es`, ...).
`maya lint --lang es` lists anything still missing Spanish; the app falls back to English audio for a lesson
that has no Spanish yet. The pronunciation guide is written separately for each audience (`pwa/guide.en.json`,
`pwa/guide.es.json`), not translated.

## Writing lessons

```bash
uv run maya draft 2             # Claude drafts curriculum/level1/lesson02.yaml from attested phrases
uv run maya attest "Bix a beel" # check any Maya string against the corpus
uv run maya lint                # attestation, item counts, duplicate ids, length
```

`maya draft` needs Anthropic credentials (`ANTHROPIC_API_KEY`). Anything the model wanted but couldn't attest is listed as `needs_review` and marked `REVIEW` in the YAML; `maya lint` fails until you resolve it.

Syllabus: `curriculum/level1/SYLLABUS.md`. Sources and licenses: `data/SOURCES.md`.

## Lesson shape

English always comes before Maya. A new phrase is introduced with its meaning, heard whole, then built up
from the end one sound at a time (`syllables`, with optional `glosses`), each fragment repeated with a gap
to say it, then prompted ("Say, how are you?") with a long pause before the answer, which is given twice.
Recalls of the phrase recur at +30 s, +2, +5 and +12 minutes, and in later lessons at +1, +2, +5, +10, +20 lessons.

Buildup fragments are **cut out of the full-phrase audio** with CTC forced alignment (`maaya/align.py`,
using the MMS Maya recognizer), because the TTS garbles fragments synthesized on their own. Every Maya
clip is also synthesized six times and the take the recognizer agrees with most is kept (`--no-rescore` to skip).

## Spike results (2026-09-22)

- `mms-tts-yua` handles the INALI orthography (apostrophes, acute accents) with zero unknown tokens and synthesizes at ~9× real time on CPU.
- Round-tripping synthesized phrases through `mms-1b-all` ASR gives ~35% character error rate after spelling normalization; full sentences transcribe well, isolated short words (buildup chunks) are the weak spot. Judge by ear: `out/lessons/POC.mp3`, `out/lessons/L1-01.mp3`, `out/spike/`.
