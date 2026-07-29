#!/usr/bin/env bash
set -euo pipefail

ROOT=$(git rev-parse --show-toplevel)
HOOK="$ROOT/hooks/mem-recall-inject.sh"
MEM="$ROOT/tools/memory/mem.py"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
export MEM_STORE="$TMP/store"
export MEM_RECALL_EVENTS="$TMP/events.jsonl"
export MEM_RECALL_RECEIPTS="$TMP/receipts"
export MEM_PY="$MEM"
mkdir -p "$MEM_STORE" "$TMP/project"
(cd "$TMP/project" && python3 "$MEM" add durable decision \
  'This durable record keeps private-body-marker out of prompt context' --headline 'Prompt candidate headline' \
  --alias 'prompt candidate' >/dev/null)

printf '{"hook_event_name":"UserPromptSubmit","prompt":"prompt candidate","cwd":"%s","session_id":"hook-session","turn_id":"turn-1"}\n' "$TMP/project" \
  | "$HOOK" > "$TMP/hook.out"
python3 - "$TMP/hook.out" <<'PY'
import json, sys
value=json.load(open(sys.argv[1], encoding="utf-8"))
context=value["hookSpecificOutput"]["additionalContext"]
assert "Prompt candidate headline" in context
assert "private-body-marker" not in context
PY

"$HOOK" --prompt 'prompt candidate' --cwd "$TMP/project" --session-id cli-session \
  --turn-id cli-turn --runtime test --format text > "$TMP/cli.out"
grep -q 'Prompt candidate headline' "$TMP/cli.out"
! grep -q 'private-body-marker' "$TMP/cli.out"

printf '%s\n' \
  '{"type":"user","uuid":"claude-user-turn","message":{"role":"user","content":"prompt candidate"}}' \
  '{"type":"assistant","uuid":"claude-assistant-turn","message":{"role":"assistant","content":"reply"}}' \
  > "$TMP/transcript.jsonl"
printf '{"hook_event_name":"UserPromptSubmit","prompt":"prompt candidate","cwd":"%s","session_id":"claude-session","transcript_path":"%s"}\n' \
  "$TMP/project" "$TMP/transcript.jsonl" | "$HOOK" > "$TMP/transcript-hook.out"
python3 - "$MEM_RECALL_RECEIPTS" <<'PY'
import hashlib, json, pathlib, sys
key=hashlib.sha256(b"memory-recall-opportunity-v1\0claude-session").hexdigest()
value=json.loads((pathlib.Path(sys.argv[1]) / f"{key}.json").read_text())
expected=hashlib.sha256(b"memory-recall-turn-v1\0transcript-user:claude-user-turn").hexdigest()
assert value["turn_digest"] == expected
PY

printf 'not json' | "$HOOK" > "$TMP/malformed.out" 2> "$TMP/malformed.err"
[ ! -s "$TMP/malformed.out" ] && [ ! -s "$TMP/malformed.err" ]

printf '{"hook_event_name":"UserPromptSubmit","prompt":"prompt candidate","cwd":"%s"}\n' "$TMP/project" \
  | AGENT_SESSION_ROLE=worker "$HOOK" > "$TMP/worker.out"
[ ! -s "$TMP/worker.out" ]

"$HOOK" --help | grep -q 'capsule candidates'
echo 'memory recall prompt bridge: PASS'
