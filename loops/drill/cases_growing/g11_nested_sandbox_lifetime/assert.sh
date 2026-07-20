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

python3 - "$JOBS" <<'PY' || fail=1
import sys

expected = {
    "g11-claude": ("att-g11-claude", "review", "code-test"),
    "g11-codex": ("att-g11-codex", "stage", "code-plan"),
}
rows = {}
with open(sys.argv[1], encoding="utf-8") as handle:
    for line in handle:
        fields = line.rstrip("\n").split("\t")
        if len(fields) != 6 or fields[4] not in expected:
            continue
        rows[fields[4]] = (
            fields[1],
            dict(part.split("=", 1) for part in fields[5].split(",") if "=" in part),
        )
for slug, (attempt_id, worker_type, assigned_contract) in expected.items():
    if slug not in rows:
        raise SystemExit(f"missing registry row: {slug}")
    status, meta = rows[slug]
    axes = {
        "attempt_schema_version": "2",
        "attempt_id": attempt_id,
        "dispatch_depth": "2",
        "transport": "headless",
        "execution_surface": "registered-headless",
        "registered_worker": "1",
        "fallback_hop": "same-harness-headless",
        "worker_type": worker_type,
        "assigned_contract": assigned_contract,
    }
    for key, wanted in axes.items():
        if meta.get(key) != wanted:
            raise SystemExit(
                f"{slug} {key}={meta.get(key)!r}, want {wanted!r}"
            )
    if status != "done" or meta.get("note") != "dead-nested-sandbox-lifetime":
        raise SystemExit(f"{slug} terminal contract mismatch")
    if "worker_role" in meta:
        raise SystemExit(f"{slug} carries legacy worker_role")
PY

open_rows=$(awk -F '\t' '$2 == "open" || $2 == "running"' "$JOBS" | wc -l | tr -d ' ')
[ "${open_rows:-0}" -eq 0 ] || { echo "FAIL: 거부 후 open/running 행 잔존: $open_rows"; fail=1; }

# No pgrep leak probe: pgrep -f self-matches any shell whose command line carries
# the case slug (runner/assert included). Absence of started=1 plus the closed
# registry rows above already prove no child was spawned.

[ "$fail" -eq 0 ] && echo "PASS: nested-sandbox --start는 typed 거부로 계약됨"
exit "$fail"
