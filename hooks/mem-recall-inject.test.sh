#!/usr/bin/env bash
# Isolated test for mem-recall-inject.sh (D-15, QA ①).
# Fully isolated via MEM_STORE temp dir — never touches real ~/.claude state.
# Hook calls $HOME/.claude/tools/memory/mem.py (deployed path) but reads MEM_STORE from env,
# so seeding into an isolated MEM_STORE is enough to exercise recall against a temp DB.
#
# QA cases:
#   T1  signal-word prompt + matching record → valid JSON additionalContext
#   T2  no-signal prompt → empty stdout, exit 0
#   T3  MEM_DISTILL=1 + signal prompt → empty stdout, exit 0 (recursion guard)
#   T4  broken stdin → exit 0, empty stdout
#   T5  signal prompt but no matching hit → empty stdout (empty-result no-op)
#   T6  result cap — char cap (Korean body) → valid JSON + chars ≤ cap
#   T7  result cap — line cap → injected lines ≤ cap
#   T8  non-UserPromptSubmit event → exit 0, empty stdout
set -u

HOOK="$(cd "$(dirname "$0")" && pwd)/mem-recall-inject.sh"
[ -f "$HOOK" ] || { echo "FAIL: hook not found at $HOOK"; exit 1; }

MEM_PY="$HOME/.claude/tools/memory/mem.py"
[ -f "$MEM_PY" ] || { echo "FAIL: deployed mem.py not found at $MEM_PY"; exit 1; }

PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); printf '  ok  %s\n' "$1"; }
bad() { FAIL=$((FAIL+1)); printf '  BAD %s\n' "$1"; }

# ---------- isolated store ----------
STORE="$(mktemp -d)"
trap 'rm -rf "$STORE"' EXIT
export MEM_STORE="$STORE"

# seed: add a record that will be found by recall (body contains the signal phrase as substring)
# Canonical signal words from hook PAT: 지난번|지난번에|예전에|이전에|전에|그때|저번에|아까
# Fixture: body contains "지난번 결정론" so prompt "지난번 결정론" is an exact substring + has signal word
python3 "$MEM_PY" add durable thread "지난번 결정론 우선 설계가 핵심이라고 배웠다" >/dev/null 2>&1
python3 "$MEM_PY" index --rebuild >/dev/null 2>&1

# ---------- helper: run hook with given event + prompt, stdout → temp file ----------
run_hook() {  # $1=event $2=prompt ; env already exported MEM_STORE
  local event="$1" prompt="$2"
  local tmpf
  tmpf="$(mktemp)"
  printf '{"hook_event_name":"%s","session_id":"testsid","prompt":"%s"}' "$event" "$prompt" \
    | bash "$HOOK" >"$tmpf" 2>/dev/null
  local rc=$?
  echo "$tmpf:$rc"  # caller uses colon-split
}

# ── T1: signal-word prompt + seeded matching record → valid JSON with additionalContext ──────────
echo "== T1: signal-word + matching record → JSON additionalContext =="

tmpf_t1="$(mktemp)"
printf '{"hook_event_name":"UserPromptSubmit","session_id":"s1","prompt":"지난번 결정론"}' \
  | bash "$HOOK" >"$tmpf_t1" 2>/dev/null
rc_t1=$?

[ "$rc_t1" = "0" ] && ok "T1: exit 0" || bad "T1: expected exit 0, got $rc_t1"

# Validate JSON via file-read (not echo — avoids \n mangling per plan (E))
json_ok_t1="$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); sys.exit(0)' "$tmpf_t1" 2>/dev/null && echo yes || echo no)"
[ "$json_ok_t1" = "yes" ] && ok "T1: stdout is valid JSON" || bad "T1: stdout not valid JSON (content: $(cat "$tmpf_t1"))"

# Check additionalContext contains the seeded body
has_body="$(python3 -c '
import json, sys
try:
    d = json.load(open(sys.argv[1]))
    ctx = d["hookSpecificOutput"]["additionalContext"]
    sys.exit(0 if "결정론" in ctx else 1)
except Exception:
    sys.exit(1)
' "$tmpf_t1" 2>/dev/null && echo yes || echo no)"
[ "$has_body" = "yes" ] && ok "T1: additionalContext contains recalled body" || bad "T1: additionalContext missing recalled body (content: $(cat "$tmpf_t1"))"

rm -f "$tmpf_t1"

# ── T2: no-signal prompt → empty stdout, exit 0 ──────────────────────────────────────────────────
echo "== T2: no-signal prompt → empty stdout =="

tmpf_t2="$(mktemp)"
printf '{"hook_event_name":"UserPromptSubmit","session_id":"s2","prompt":"오늘 날씨는 어때요"}' \
  | bash "$HOOK" >"$tmpf_t2" 2>/dev/null
rc_t2=$?

[ "$rc_t2" = "0" ] && ok "T2: exit 0" || bad "T2: expected exit 0, got $rc_t2"
out_t2="$(cat "$tmpf_t2")"
[ -z "$out_t2" ] && ok "T2: empty stdout (no-signal no-op)" || bad "T2: stdout not empty: $out_t2"
rm -f "$tmpf_t2"

# ── T3: MEM_DISTILL=1 + signal prompt → empty stdout, exit 0 (recursion guard) ─────────────────
echo "== T3: MEM_DISTILL=1 + signal prompt → recursion guard =="

tmpf_t3="$(mktemp)"
printf '{"hook_event_name":"UserPromptSubmit","session_id":"s3","prompt":"지난번에 뭘 했죠"}' \
  | MEM_DISTILL=1 bash "$HOOK" >"$tmpf_t3" 2>/dev/null
rc_t3=$?

[ "$rc_t3" = "0" ] && ok "T3: exit 0 under MEM_DISTILL=1" || bad "T3: expected exit 0, got $rc_t3"
out_t3="$(cat "$tmpf_t3")"
[ -z "$out_t3" ] && ok "T3: empty stdout (distill guard no-op)" || bad "T3: stdout not empty under MEM_DISTILL=1: $out_t3"
rm -f "$tmpf_t3"

# ── T4: broken stdin → exit 0, empty stdout ──────────────────────────────────────────────────────
echo "== T4: broken stdin → exit 0 fail-safe =="

tmpf_t4="$(mktemp)"
printf 'not json at all' | bash "$HOOK" >"$tmpf_t4" 2>/dev/null
rc_t4=$?

[ "$rc_t4" = "0" ] && ok "T4: exit 0 on broken stdin" || bad "T4: expected exit 0, got $rc_t4"
out_t4="$(cat "$tmpf_t4")"
[ -z "$out_t4" ] && ok "T4: empty stdout on broken stdin" || bad "T4: stdout not empty: $out_t4"
rm -f "$tmpf_t4"

# ── T5: signal prompt but no matching hit → empty stdout (empty-result no-op) ───────────────────
# Per plan (C): seed ONE unrelated record (store exists), signal-word prompt with no matching terms
echo "== T5: signal-word prompt + no matching hit → empty-result no-op =="

# Store already has "결정론" record. Use a signal word with totally unrelated query terms.
# "그때 xyznonexistent12345" — signal word "그때" but no body contains "xyznonexistent12345"
tmpf_t5="$(mktemp)"
printf '{"hook_event_name":"UserPromptSubmit","session_id":"s5","prompt":"그때 xyznonexistent12345"}' \
  | bash "$HOOK" >"$tmpf_t5" 2>/dev/null
rc_t5=$?

[ "$rc_t5" = "0" ] && ok "T5: exit 0 on no-hit" || bad "T5: expected exit 0, got $rc_t5"
out_t5="$(cat "$tmpf_t5")"
[ -z "$out_t5" ] && ok "T5: empty stdout (no-hit no-op)" || bad "T5: stdout not empty on no-hit: $out_t5"
rm -f "$tmpf_t5"

# ── T6: char cap — Korean body, MEM_RECALL_CHARS small → valid JSON + chars ≤ cap ───────────────
echo "== T6: char cap (MEM_RECALL_CHARS=50) → valid JSON + len ≤ cap =="

# Seed a record whose body contains the exact prompt as a substring (plan (C): exact substring match)
# prompt = "예전에 긴 내용 캡테스트" must appear verbatim in the body
python3 "$MEM_PY" add durable thread "예전에 긴 내용 캡테스트 이것은 글자수캡 테스트용으로 사용되는 매우 긴 바디입니다 계속됩니다 더 늘립니다" >/dev/null 2>&1
python3 "$MEM_PY" index --rebuild >/dev/null 2>&1

tmpf_t6="$(mktemp)"
printf '{"hook_event_name":"UserPromptSubmit","session_id":"s6","prompt":"예전에 긴 내용 캡테스트"}' \
  | MEM_RECALL_CHARS=50 bash "$HOOK" >"$tmpf_t6" 2>/dev/null
rc_t6=$?

[ "$rc_t6" = "0" ] && ok "T6: exit 0 with char cap" || bad "T6: expected exit 0, got $rc_t6"

python3 -c '
import json, sys
try:
    d = json.load(open(sys.argv[1]))
    ctx = d["hookSpecificOutput"]["additionalContext"]
    # body = additionalContext after the label line. The hook slices the recall block to
    # MEM_RECALL_CHARS=50 chars (python char-slice b[:50]); the label is prepended and exempt.
    # Assert BOTH: valid JSON (escaping survived the Korean char slice) AND body ≤ 50 chars (cap pinned).
    body = ctx[ctx.index("\n")+1:] if "\n" in ctx else ctx
    print("cap_ok" if len(body) <= 50 else f"cap_exceeded: {len(body)} chars")
except Exception as e:
    print(f"invalid: {e}")
' "$tmpf_t6" | grep -q "^cap_ok" \
  && ok "T6: char cap enforced — body ≤ MEM_RECALL_CHARS(50) AND valid JSON (Korean char slice)" \
  || bad "T6: char cap not enforced / invalid JSON (content: $(cat "$tmpf_t6"))"

rm -f "$tmpf_t6"

# ── T7: line cap (MEM_RECALL_LINES=2) → injected lines ≤ cap ────────────────────────────────────
echo "== T7: line cap (MEM_RECALL_LINES=2) =="

# Each record's body must contain the exact query as a substring.
# prompt = "아까 LINE_CAP_TEST_라인캡" — each body starts with this exact phrase
for i in 1 2 3 4 5; do
  python3 "$MEM_PY" add durable thread "아까 LINE_CAP_TEST_라인캡 번호 ${i} 기억 내용입니다 라인캡 테스트 목적" >/dev/null 2>&1
done
python3 "$MEM_PY" index --rebuild >/dev/null 2>&1

tmpf_t7="$(mktemp)"
printf '{"hook_event_name":"UserPromptSubmit","session_id":"s7","prompt":"아까 LINE_CAP_TEST_라인캡"}' \
  | MEM_RECALL_LINES=2 bash "$HOOK" >"$tmpf_t7" 2>/dev/null
rc_t7=$?

[ "$rc_t7" = "0" ] && ok "T7: exit 0 with line cap" || bad "T7: expected exit 0, got $rc_t7"

python3 -c '
import json, sys
try:
    d = json.load(open(sys.argv[1]))
    ctx = d["hookSpecificOutput"]["additionalContext"]
    # body = additionalContext after the label line. The hook caps the recall block to
    # MEM_RECALL_LINES=2 via head -n (recall header + ≤1 hit-line = ≤2 block lines), then prepends the label.
    # Single-branch assert (no OR fallback): the recall block itself is ≤ MEM_RECALL_LINES(2) lines.
    body = ctx[ctx.index("\n")+1:] if "\n" in ctx else ctx
    nlines = len(body.splitlines())
    print("cap_ok" if nlines <= 2 else f"cap_exceeded: {nlines} block lines")
except Exception as e:
    print(f"error: {e}")
' "$tmpf_t7" | grep -q "^cap_ok" \
  && ok "T7: line cap enforced — recall block ≤ MEM_RECALL_LINES(2) lines" \
  || bad "T7: line cap not enforced (content: $(cat "$tmpf_t7"))"

rm -f "$tmpf_t7"

# ── T8: non-UserPromptSubmit event → exit 0, empty stdout ────────────────────────────────────────
echo "== T8: non-UserPromptSubmit event (SessionStart) → exit 0 no-op =="

tmpf_t8="$(mktemp)"
printf '{"hook_event_name":"SessionStart","session_id":"s8","prompt":"지난번 결정론"}' \
  | bash "$HOOK" >"$tmpf_t8" 2>/dev/null
rc_t8=$?

[ "$rc_t8" = "0" ] && ok "T8: exit 0 on SessionStart event" || bad "T8: expected exit 0, got $rc_t8"
out_t8="$(cat "$tmpf_t8")"
[ -z "$out_t8" ] && ok "T8: empty stdout on non-UserPromptSubmit" || bad "T8: stdout not empty: $out_t8"
rm -f "$tmpf_t8"

echo
echo "RESULT: PASS=$PASS FAIL=$FAIL"
[ "$FAIL" = "0" ]
