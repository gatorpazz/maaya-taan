---
name: voice-check
description: Audit the synthetic Maya voice for a lesson: list the clips the Maya speech recognizer agreed with least, export a short excerpt for listening, and suggest chunk or phrasing changes. Use when a phrase sounds wrong or before publishing a batch.
argument-hint: "[lesson number]"
allowed-tools: Bash(uv run maya *), Bash(uv run python *), Bash(ffprobe *), Read
---

Check the Maya audio quality for lesson `$ARGUMENTS` (default: all rendered lessons).

1. `uv run maya voice-report [N]` prints every distinct Maya clip from the last renders with the character error rate
   between its text and what the MMS recognizer heard on the best of six takes. Anything above 40% on a phrase of 3+
   words is suspicious; isolated one-syllable fragments are always noisy and are cut from full-phrase audio anyway, so
   weigh them lightly.
2. For suspicious full phrases, look at the YAML: is there an attested shorter variant (`uv run maya attest`), or can the
   phrase be split into two items? Recognizer failures on `k'aaba'`-type words with several apostrophes are a known
   weakness of the voice, not of the lesson; say so rather than rewriting good content.
3. Export an excerpt the user can listen to: build a `Script` from the lesson's timeline segments for the worst 2–3 items
   (intro through first answer) and render it with `maaya.render.export_mp3` to `out/spike/voice_check_LN.mp3`
   (see `scripts/poc_lesson.py` for the pattern; TTS results are cached so this takes seconds).
4. Report: the ranked list, the excerpt path, and concrete YAML edits if any. The user's ear decides; you never change
   attested Maya to make the recognizer happier.
