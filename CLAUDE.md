# Maaya T'aan

Pimsleur-style audio course generator for Yucatec Maya, plus the static phone app that plays it.
Live: https://maaya-taan.gatorpazz.workers.dev. Source: https://github.com/gatorpazz/maaya-taan.

## Non-negotiable content rules

- **Never invent Maya.** Every Maya string in `curriculum/` must be attested in `lexicon.db` (YUA-ES-CCC corpus or
  Wiktionary) or marked `attested_by: [REVIEW]`. Check any string with `uv run maya attest "..."`. `maya lint` enforces it.
- **The narrator never says a Maya word.** Narrator copy (English or Spanish) gives the meaning; the Maya voice says the Maya.
  Meaning always comes *before* the Maya.
- **Buildup chunks are substrings.** `syllables` is the backward buildup in speaking order, ending with the full phrase; every
  chunk must be a substring of the phrase, because fragments are *cut out of the full-phrase audio* by forced alignment
  (the TTS garbles fragments synthesized alone). `glosses` keys are chunks or words of the phrase.
- **Spelling is INALI 2014**: apostrophes for glottalization, doubled vowels for length, acute accents for high tone.
- **Both languages.** Every English teaching field has a Spanish twin (`es`, `note_es`, `cues_es`, `glosses_es`, `prompt_es`,
  `setting_es`, `title_es`, `grammar_note_es`). Write Spanish for a Spanish speaker; don't translate word by word.
  `uv run maya lint --lang es` lists what's missing.

## How the pieces fit

```
curriculum/level1/lessonNN.yaml  →  maaya/planner.py (timed script, GIR scheduling)  →  maaya/render.py
   ↑ maya draft (Claude Code CLI)      timing from maaya/timing.py (calibrated)          MMS Maya voice, best-of-6 by ASR
                                                                                        Kokoro narrator (en af_heart / es ef_dora)
out/lessons/L1-NN.{en,es}.mp3 + .json timeline + .lesson.json + L1-NN.clips/  →  maya build → site/  →  maya deploy (Cloudflare)
```

- Lessons render once per learner state. The public course is rendered by `maya build`, which walks lessons in order with a
  canonical fresh-learner state (`out/canonical-learner.json`), so lesson N contains the reviews a learner who did 1..N-1 needs.
- `learner.json` at the repo root is the author's *personal* progress (`maya render N` / `maya complete N`). Don't confuse it with the canonical one.
- The app (`pwa/`) is static: progress lives in localStorage; the review drill uses the isolated clips.
- `worker.js` exists only to answer HTTP byte-range requests for audio on Cloudflare; iOS Safari refuses media without them.

## Commands you'll use

| Task | Command |
|---|---|
| Which lesson is next, and its syllabus row | `uv run maya next-lesson` |
| Draft lesson N (Claude Code CLI, your subscription) | `uv run maya draft N` |
| Validate all lessons (add `--lang es` for Spanish coverage) | `uv run maya lint` |
| Estimated length / segment count without audio | `uv run maya plan N --lang en` |
| Render lessons 1..N in both languages + assemble `site/` | `uv run maya build --upto N` |
| Preview `site/` on the LAN | `uv run maya serve` |
| Publish `site/` to Cloudflare | `uv run maya deploy` |
| Worst-recognized Maya clips from the last renders | `uv run maya voice-report` |
| Tests | `uv run pytest -q` |

Rendering costs about 2 min per lesson per language on this Mac (first time; TTS is cached after).
`maya build` re-renders from cache quickly. Always `maya lint` before `maya build`.

## Conventions

- Python 3.12, `uv`, pydantic models, typer CLI. Tests in `tests/` (pure planner/learner tests, no audio).
- Shell here has `noclobber`: use `>|` to overwrite files from heredocs.
- Commit messages end with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
- Don't commit `out/`, `site/`, `data/raw/`, `.cache/`, `lexicon.db`, `learner.json` (all gitignored).
- Data licenses in `data/SOURCES.md`; the Maya voice model is CC BY-NC, so the course stays non-commercial.
- Skills: `/draft-lesson`, `/review-lesson`, `/publish`, `/voice-check`. A hook lints any lesson YAML you edit.
