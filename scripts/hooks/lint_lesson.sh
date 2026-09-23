#!/usr/bin/env bash
# PostToolUse hook: after Claude edits a lesson YAML, lint it (both languages) and hand problems back as context.
set -u
f=$(jq -r '.tool_input.file_path // .tool_response.filePath // empty' 2>/dev/null)
case "$f" in
  */curriculum/*.yaml|*/curriculum/*.yml) ;;
  *) exit 0 ;;
esac
cd "$(dirname "$0")/../.." || exit 0
out=$( { uv run maya lint 2>&1; uv run maya lint --lang es 2>&1; } | grep -vE "lessons, 0 problems$" | sed -n '1,40p')
if [ -n "$out" ]; then
  jq -n --arg o "$out" '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: ("maya lint after editing " + "'"$(basename "$f")"'" + ":\n" + $o)}}'
fi
exit 0
