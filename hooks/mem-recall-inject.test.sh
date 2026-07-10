#!/usr/bin/env bash
# Isolated contract tests for mem-recall-inject.sh.
# A stub mem.py records argv/cwd and models the shared --auto engine's hit/empty output.
set -u

HOOK="$(cd "$(dirname "$0")" && pwd)/mem-recall-inject.sh"
[ -f "$HOOK" ] || { echo "FAIL: hook not found at $HOOK"; exit 1; }

PASS=0
FAIL=0
ok()  { PASS=$((PASS + 1)); printf '  ok  %s\n' "$1"; }
bad() { FAIL=$((FAIL + 1)); printf '  BAD %s\n' "$1"; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
HARNESS="$TMP/harness"
WORK="$TMP/project cwd"
LOG="$TMP/calls.jsonl"
mkdir -p "$HARNESS/tools/memory" "$WORK/.agent_reports"

cat > "$HARNESS/tools/memory/mem.py" <<'PY'
#!/usr/bin/env python3
import json
import os
import sys

entry = {"argv": sys.argv[1:], "cwd": os.getcwd()}
with open(os.environ["MEM_STUB_LOG"], "a", encoding="utf-8") as fh:
    fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

if len(sys.argv) < 5 or sys.argv[1] != "recall":
    raise SystemExit(64)
prompt = sys.argv[2]
if prompt in {"오늘 날씨는 어때요", "generic empty result"}:
    raise SystemExit(0)
if prompt == "cap fixture":
    payload = "가" * 500
    print("# 관련 기억 (자동 회상)")
    for idx in range(1, 6):
        print(f"  [durable/project/lesson] cap-{idx}: {payload}")
    raise SystemExit(0)

print("# 관련 기억 (자동 회상)")
print(f"  [durable/project/lesson] auto-hit: recalled {prompt}")
PY

run_stdin() {
  local event=$1 prompt=$2 cwd=$3 outfile=$4
  printf '{"hook_event_name":"%s","session_id":"test-session","prompt":"%s","cwd":"%s"}\n' \
    "$event" "$prompt" "$cwd" \
    | AGENT_HOME="$HARNESS" MEM_STUB_LOG="$LOG" bash "$HOOK" >"$outfile" 2>/dev/null
}

last_call_matches() {
  local prompt=$1 cwd=$2
  python3 - "$LOG" "$prompt" "$cwd" <<'PY'
import json
import sys

rows = [json.loads(line) for line in open(sys.argv[1], encoding="utf-8") if line.strip()]
expected = ["recall", sys.argv[2], "--auto", "--limit", "3"]
raise SystemExit(0 if rows and rows[-1] == {"argv": expected, "cwd": sys.argv[3]} else 1)
PY
}

json_context_has() {
  local file=$1 needle=$2
  python3 - "$file" "$needle" <<'PY'
import json
import sys

try:
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    output = data["hookSpecificOutput"]
    valid = output["hookEventName"] == "UserPromptSubmit" and sys.argv[2] in output["additionalContext"]
except Exception:
    valid = False
raise SystemExit(0 if valid else 1)
PY
}

echo "== T1: no-signal project prompt reaches shared auto engine =="
OUT="$TMP/t1.out"
: > "$LOG"
run_stdin "UserPromptSubmit" "stage-dispatch handoff 점검" "$WORK" "$OUT"
rc=$?
[ "$rc" = 0 ] && ok "T1: exit 0" || bad "T1: exit $rc"
last_call_matches "stage-dispatch handoff 점검" "$WORK" \
  && ok "T1: argv=recall <prompt> --auto --limit 3 and cwd preserved" \
  || bad "T1: shared engine argv/cwd mismatch: $(cat "$LOG")"
json_context_has "$OUT" "stage-dispatch handoff 점검" \
  && ok "T1: Claude payload emits JSON additionalContext" \
  || bad "T1: missing JSON context: $(cat "$OUT")"

echo "== T2: signal-word prompt uses the same auto path =="
OUT="$TMP/t2.out"
: > "$LOG"
AGENT_HOME="$HARNESS" MEM_STUB_LOG="$LOG" bash "$HOOK" \
  --prompt "지난번 stage-dispatch 확인" --cwd "$WORK" --session-id cli-session \
  --format text >"$OUT" 2>/dev/null
rc=$?
[ "$rc" = 0 ] && ok "T2: exit 0" || bad "T2: exit $rc"
last_call_matches "지난번 stage-dispatch 확인" "$WORK" \
  && ok "T2: signal prompt also calls --auto --limit 3" \
  || bad "T2: signal prompt bypassed shared engine: $(cat "$LOG")"
grep -q "고신뢰 매칭" "$OUT" && grep -q "지난번 stage-dispatch 확인" "$OUT" \
  && ok "T2: text adapter output contains recalled hit" \
  || bad "T2: text output mismatch: $(cat "$OUT")"

echo "== T3: generic prompt is delegated; empty engine result is a no-op =="
OUT="$TMP/t3.out"
: > "$LOG"
run_stdin "UserPromptSubmit" "오늘 날씨는 어때요" "$WORK" "$OUT"
rc=$?
[ "$rc" = 0 ] && ok "T3: exit 0" || bad "T3: exit $rc"
last_call_matches "오늘 날씨는 어때요" "$WORK" \
  && ok "T3: generic prompt still reaches shared classifier" \
  || bad "T3: generic prompt was not delegated: $(cat "$LOG")"
[ ! -s "$OUT" ] && ok "T3: empty auto result injects nothing" || bad "T3: unexpected output: $(cat "$OUT")"

echo "== T4: distiller recursion and empty prompt skip engine =="
OUT="$TMP/t4.out"
: > "$LOG"
printf '{"hook_event_name":"UserPromptSubmit","prompt":"stage-dispatch","cwd":"%s"}\n' "$WORK" \
  | MEM_DISTILL=1 AGENT_HOME="$HARNESS" MEM_STUB_LOG="$LOG" bash "$HOOK" >"$OUT" 2>/dev/null
rc=$?
[ "$rc" = 0 ] && [ ! -s "$OUT" ] && [ ! -s "$LOG" ] \
  && ok "T4a: MEM_DISTILL skips engine and output" \
  || bad "T4a: distiller guard failed"
run_stdin "UserPromptSubmit" "" "$WORK" "$OUT"
rc=$?
[ "$rc" = 0 ] && [ ! -s "$OUT" ] && [ ! -s "$LOG" ] \
  && ok "T4b: empty prompt skips engine and output" \
  || bad "T4b: empty prompt guard failed"

echo "== T5: hook enforces top-3 and 1200-char maximum =="
OUT="$TMP/t5.out"
: > "$LOG"
printf '{"hook_event_name":"UserPromptSubmit","prompt":"cap fixture","cwd":"%s"}\n' "$WORK" \
  | MEM_RECALL_CHARS=5000 AGENT_HOME="$HARNESS" MEM_STUB_LOG="$LOG" bash "$HOOK" >"$OUT" 2>/dev/null
python3 - "$OUT" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
context = data["hookSpecificOutput"]["additionalContext"]
valid = len(context) <= 1200 and "cap-1" in context and "cap-3" in context and "cap-4" not in context
raise SystemExit(0 if valid else 1)
PY
rc=$?
[ "$rc" = 0 ] \
  && ok "T5a: context body <=1200 chars and no fourth hit" \
  || bad "T5a: fixed cap failed"
OUT_SMALL="$TMP/t5-small.out"
printf '{"hook_event_name":"UserPromptSubmit","prompt":"cap fixture","cwd":"%s"}\n' "$WORK" \
  | MEM_RECALL_CHARS=80 AGENT_HOME="$HARNESS" MEM_STUB_LOG="$LOG" bash "$HOOK" >"$OUT_SMALL" 2>/dev/null
python3 - "$OUT_SMALL" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
context = data["hookSpecificOutput"]["additionalContext"]
raise SystemExit(0 if len(context) <= 80 else 1)
PY
rc=$?
[ "$rc" = 0 ] && ok "T5b: smaller UTF-8-safe env cap remains supported" || bad "T5b: small cap failed"

echo "== T6: irrelevant runtime events and malformed payloads are no-ops =="
OUT="$TMP/t6.out"
: > "$LOG"
run_stdin "SessionStart" "stage-dispatch" "$WORK" "$OUT"
rc=$?
[ "$rc" = 0 ] && [ ! -s "$OUT" ] && [ ! -s "$LOG" ] \
  && ok "T6a: non-UserPromptSubmit skips engine" \
  || bad "T6a: event guard failed"
printf 'not json' | AGENT_HOME="$HARNESS" MEM_STUB_LOG="$LOG" bash "$HOOK" >"$OUT" 2>/dev/null
rc=$?
[ "$rc" = 0 ] && [ ! -s "$OUT" ] && [ ! -s "$LOG" ] \
  && ok "T6b: malformed payload fails open without recall" \
  || bad "T6b: malformed payload handling failed"

echo "== T7: non-project and untracked cwd skip automatic recall =="
OUT="$TMP/t7.out"
PLAIN="$TMP/plain cwd"; mkdir -p "$PLAIN"
: > "$LOG"
run_stdin "UserPromptSubmit" "stage-dispatch" "$PLAIN" "$OUT"
rc=$?
[ "$rc" = 0 ] && [ ! -s "$OUT" ] && [ ! -s "$LOG" ] \
  && ok "T7a: non-project cwd skips engine" \
  || bad "T7a: non-project gate failed"
: > "$WORK/.agent_reports/.untracked.test-session"
run_stdin "UserPromptSubmit" "stage-dispatch" "$WORK" "$OUT"
rc=$?
[ "$rc" = 0 ] && [ ! -s "$OUT" ] && [ ! -s "$LOG" ] \
  && ok "T7b: session-scoped untracked flag skips engine" \
  || bad "T7b: untracked gate failed"
rm -f "$WORK/.agent_reports/.untracked.test-session"
: > "$WORK/.agent_reports/.untracked.cli-session"
AGENT_HOME="$HARNESS" MEM_STUB_LOG="$LOG" bash "$HOOK" \
  --prompt "stage-dispatch" --cwd "$WORK" --session-id cli-session --format text >"$OUT" 2>/dev/null
rc=$?
[ "$rc" = 0 ] && [ ! -s "$OUT" ] && [ ! -s "$LOG" ] \
  && ok "T7c: CLI-projected session id honors untracked flag" \
  || bad "T7c: CLI session propagation failed"
rm -f "$WORK/.agent_reports/.untracked.cli-session"

echo
echo "RESULT: PASS=$PASS FAIL=$FAIL"
[ "$FAIL" = 0 ]
