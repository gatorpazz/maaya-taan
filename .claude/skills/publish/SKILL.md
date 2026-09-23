---
name: publish
description: Build and publish the Maaya T'aan course: lint, render lessons 1..N in both languages, assemble the static site, verify durations and review scheduling, deploy to Cloudflare, verify the live site, and commit. Use when asked to publish, deploy, ship, or release lessons.
argument-hint: "[--upto N] [--no-deploy]"
allowed-tools: Bash(uv run maya *), Bash(uv run pytest *), Bash(ffprobe *), Bash(curl *), Bash(git *), Bash(ls *), Bash(python3 *), Read
---

Publish the course. Arguments: `$ARGUMENTS`.

1. `uv run pytest -q`, `uv run maya lint`, `uv run maya lint --lang es`. Stop and report if anything fails.
2. Decide N: `--upto N` if given, else the highest `curriculum/level1/lessonNN.yaml`.
3. `uv run maya build --upto N` (renders both languages in order with canonical progress; ~2 min per new lesson per
   language, cached ones are fast). Watch for `Traceback`.
4. Verify locally: every `site/lessons/L1-NN.{en,es}.mp3` exists; `ffprobe` durations are 25–35 min; the
   `site/manifest.json` lists N lessons with both variants; for N ≥ 2, the lesson N timeline contains review recalls of
   earlier items (segment notes ending in `:s2`, `:s3`, `:s4a` whose item id belongs to an earlier lesson).
5. Unless `--no-deploy`: `uv run maya deploy`. Then, after a few seconds, check the live site with cache-busting query
   strings: `manifest.json` lists N lessons; a `Range: bytes=0-999` request to a new lesson's MP3 returns 206.
6. Commit the curriculum and any code changes (never `site/`, `out/`) with a message that names the lessons published,
   ending with the project's Co-Authored-By trailer, and push.
7. Report: what's live, durations, and anything skipped.
