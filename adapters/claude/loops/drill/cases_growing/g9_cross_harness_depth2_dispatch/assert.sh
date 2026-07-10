#!/bin/bash
# hard: depth-2 cross-harness registry rows must be parseable by fleet and connected to depth-1 owner.
set -u
WORK=$1
T=$2
REPO="$WORK/repo"
JOBS="$REPO/.dispatch/jobs.log"
fail=0

[ -f "$JOBS" ] || { echo "FAIL: .dispatch/jobs.log 없음"; exit 1; }

bad_fields=$(awk -F '\t' 'NF != 6 {print NR ":" NF}' "$JOBS")
if [ -n "$bad_fields" ]; then
  echo "FAIL: jobs.log 6필드 위반: $bad_fields"
  fail=1
fi

bad_status=$(awk -F '\t' '$2 !~ /^(open|running)$/ {print NR ":" $2}' "$JOBS")
if [ -n "$bad_status" ]; then
  echo "FAIL: fleet live registry status(open/running) 위반: $bad_status"
  fail=1
fi

if awk -F '\t' '$6 ~ / / || $6 !~ /,/ {bad=1} END {exit bad ? 0 : 1}' "$JOBS"; then
  echo "FAIL: pipe metadata는 comma-separated key=value 여야 함"
  fail=1
fi

owner=$(awk -F '\t' '$5 == "xh-depth2-owner" && $6 ~ /capability=autopilot-code/ && $6 ~ /depth=1/ && $6 ~ /harness=codex/ && $6 ~ /worker_role=capability-owner/ && $6 ~ /owner=autopilot-code/ {n++} END {print n+0}' "$JOBS")
[ "$owner" -ge 1 ] || { echo "FAIL: autopilot-code codex depth-1 owner row 없음"; fail=1; }

children=$(awk -F '\t' '$6 ~ /parent=xh-depth2-owner/ && $6 ~ /depth=2/ {n++} END {print n+0}' "$JOBS")
[ "$children" -ge 2 ] || { echo "FAIL: depth-2 child row 2개 미만"; fail=1; }

grep -q 'parent_sid=drill-parent-session' "$JOBS" || { echo "FAIL: parent_sid 연결 메타 없음"; fail=1; }
grep -q 'parent_cwd=' "$JOBS" || { echo "FAIL: parent_cwd fallback 메타 없음"; fail=1; }
grep -q 'parent=xh-depth2-owner.*harness=claude\|harness=claude.*parent=xh-depth2-owner' "$JOBS" || { echo "FAIL: depth-2 claude worker 없음"; fail=1; }
grep -q 'parent=xh-depth2-owner.*harness=opencode\|harness=opencode.*parent=xh-depth2-owner' "$JOBS" || { echo "FAIL: depth-2 opencode worker 없음"; fail=1; }

if grep -Eq '(^|[[:space:]/])(codex|claude|opencode)([[:space:]]|$)' "$T"; then
  echo "WARN: transcript mentions runtime command names; ensure they were not launched"
fi

CASE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
HARNESS_ROOT=$(git -C "$CASE_DIR" rev-parse --show-toplevel 2>/dev/null || pwd)
PYTHONPATH="$HARNESS_ROOT/tools" JOBS="$JOBS" python3 - <<'PY' || fail=1
import os
from fleet.collectors import dispatch
jobs = dispatch.collect(jobs_path=os.environ["JOBS"])
owner = [
    j for j in jobs
    if j.slug == "xh-depth2-owner"
    and j.key == "code"
    and j.depth == 1
    and j.harness == "codex"
    and j.worker_role == "capability-owner"
    and j.capability_owner == "autopilot-code"
]
children = [j for j in jobs if j.parent_slug == "xh-depth2-owner" and j.depth == 2]
harnesses = {j.harness for j in children}
if not owner:
    raise SystemExit("fleet parse missing autopilot-code depth-1 owner")
if not {"claude", "opencode"}.issubset(harnesses):
    raise SystemExit(f"fleet parse missing cross-harness depth2 children: {sorted(harnesses)}")
if not all(j.is_child for j in children):
    raise SystemExit("fleet parse did not mark depth2 children as child jobs")
print("PASS: fleet collector parses depth-1 owner + cross-harness depth-2 children")
PY

exit $fail
