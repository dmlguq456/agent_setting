#!/bin/bash
# hard: provisional detached selection is promoted before attempt_id registration;
# fallback_hop accounting must never see dead-nested-sandbox-lifetime.
set -u
WORK=$1
REPO="$WORK/repo"
OUT="$REPO/wrapper_output.txt"
fail=0

[ -f "$REPO/skill_result.md" ] || { echo "FAIL: skill_result.md 없음"; fail=1; }
[ -f "$OUT" ] || { echo "FAIL: wrapper_output.txt 없음"; exit 1; }

grep -q 'lifecycle_exit=0' "$OUT" || { echo "FAIL: lifecycle unit 회귀"; fail=1; }
grep -q 'codex_claude_exit=0' "$OUT" || { echo "FAIL: Codex/Claude 반복 fixture 회귀"; fail=1; }
grep -q 'opencode_exit=0' "$OUT" || { echo "FAIL: OpenCode parity 회귀"; fail=1; }
if grep -q 'dead-nested-sandbox-lifetime\|reason=nested-sandbox-lifetime' "$OUT"; then
  echo "FAIL: nested-sandbox 실패가 상위로 노출됨"
  fail=1
fi

[ "$fail" -eq 0 ] && echo "PASS: wrapper prelaunch promotion 반복 fixture 상위 실패 노출 0"
exit "$fail"
