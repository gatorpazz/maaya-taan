---
name: draft-lesson
description: Draft the next lesson (or lesson N) of the Maaya T'aan course from corpus-attested phrases, lint it in both languages, run the pedagogy review, and fix what the review finds. Use when asked to write, draft, add, or continue lessons.
argument-hint: "[lesson number, default: next] [--no-review]"
allowed-tools: Bash(uv run maya *), Bash(uv run pytest *), Read, Edit, Agent
---

Draft one lesson end to end. Arguments: `$ARGUMENTS` (a lesson number, or empty for the next one).

1. **Find the slot.** Run `uv run maya next-lesson` (or use the number given). Read its syllabus row and the previous
   lesson's YAML so you know what's already taught and the tone of the notes.
2. **Draft.** `uv run maya draft N` (add `--force` only if the user asked to redo an existing lesson). This runs the
   Claude Code CLI under the user's subscription, constrained to attested phrases, and writes `curriculum/level1/lessonNN.yaml`.
   Note anything it printed under "could not attest".
3. **Lint.** `uv run maya lint` and `uv run maya lint --lang es`. Fix problems by editing the YAML directly:
   chunks must be substrings of the phrase; glosses key chunks or words; 6–12 items; ~26–34 min estimated;
   no `REVIEW` left (replace with an attested alternative found via `uv run maya attest "..."`, or drop the item).
4. **Review.** Unless `--no-review`: run the `lesson-reviewer` agent on the file (Agent tool, subagent_type
   `lesson-reviewer`, give it the path). Apply the findings that are correct; push back on ones that would break
   attestation. Re-run both lints after edits.
5. **Sanity check the length.** `uv run maya plan N --lang en` and `--lang es`; both should land near 30 minutes.
6. **Report** in a few lines: the lesson title, the items, anything you changed after review, and anything the user
   should listen to. Do not build or deploy; that's `/publish`.
