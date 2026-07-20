#!/bin/bash
# hard: inside a PID-namespace sandbox both wrappers must refuse --start with the
# typed nested-sandbox-lifetime reason — never started=1, never a live child.
set -u
WORK=$1
T=$2
REPO="$WORK/repo"
OUT="$REPO/wrapper_output.txt"
JOBS="$REPO/.dispatch/jobs.log"
fail=0

[ -f "$REPO/skill_result.md" ] || { echo "FAIL: skill_result.md 없음"; fail=1; }
[ -f "$OUT" ] || { echo "FAIL: wrapper_output.txt 없음"; exit 1; }

refusals=$(grep -c 'reason=nested-sandbox-lifetime' "$OUT")
[ "${refusals:-0}" -ge 2 ] || { echo "FAIL: typed 거부 2건 미만: $refusals"; fail=1; }

grep -q 'claude_exit=77' "$OUT" || { echo "FAIL: claude wrapper exit 77 아님"; fail=1; }
grep -q 'codex_exit=77' "$OUT" || { echo "FAIL: codex wrapper exit 77 아님"; fail=1; }

if grep -q 'started=1' "$OUT"; then
  echo "FAIL: 가드 회귀 — 네임스페이스 안에서 spawn이 진행됨(started=1)"
  fail=1
fi

[ -f "$JOBS" ] || { echo "FAIL: jobs.log 없음"; exit 1; }
notes=$(grep -c 'note=dead-nested-sandbox-lifetime' "$JOBS")
[ "${notes:-0}" -ge 2 ] || { echo "FAIL: registry typed note 2건 미만: $notes"; fail=1; }

open_rows=$(awk -F '\t' '$2 == "open" || $2 == "running"' "$JOBS" | wc -l | tr -d ' ')
[ "${open_rows:-0}" -eq 0 ] || { echo "FAIL: 거부 후 open/running 행 잔존: $open_rows"; fail=1; }

# No pgrep leak probe: pgrep -f self-matches any shell whose command line carries
# the case slug (runner/assert included). Absence of started=1 plus the closed
# registry rows above already prove no child was spawned.

[ "$fail" -eq 0 ] && echo "PASS: nested-sandbox --start는 typed 거부로 계약됨"
exit "$fail"
