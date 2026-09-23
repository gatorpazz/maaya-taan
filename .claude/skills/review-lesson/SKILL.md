---
name: review-lesson
description: Pedagogical and linguistic review of one lesson YAML (attestation, Pimsleur progression, chunking, cue quality, Spanish naturalness). Use after drafting or when a lesson feels off.
argument-hint: "<lesson number or path>"
context: fork
agent: lesson-reviewer
---

Review `$ARGUMENTS` (a lesson number under `curriculum/level1/`, or a YAML path) against the rubric in your instructions.
Run `uv run maya lint` and `uv run maya lint --lang es` first and include their output. Check every Maya string that is
not exact-attested with `uv run maya attest "<string>"`. Report findings ranked by severity with the exact YAML field to
change and the proposed replacement text. Do not edit files.
