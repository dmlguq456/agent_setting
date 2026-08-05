#!/bin/bash
# g_stage_dispatch_blocked_leg — a BLOCKED codex leg leaves an open row and the
# owner must recover, exactly once, without breadth-close (fixes 3+4, plan.md
# §7). AXIS=static: no model turn ran; this drives the real reconcile path.
set -u
WORK=$1; T=$2
CASE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
HARNESS_ROOT=$(CDPATH= cd -- "$CASE_DIR/../../../.." && pwd)
fail=0

# 1. Run the real runtime path — reconcile_finished_children, not a
#    reimplementation.
out=$(AGENT_HOME="$HARNESS_ROOT" python3 - "$WORK" "$HARNESS_ROOT" <<'PY'
import sys
sys.path.insert(0, sys.argv[2] + "/utilities")
from pathlib import Path
import dispatch_completion_join as JOIN

work = Path(sys.argv[1])
jobs = work / "jobs.log"
parent = (work / ".pre/parent_attempt_id.txt").read_text().strip()
rows = {row.attempt_id: row for row in JOIN.current_children(jobs, parent)}
unresolved = {a for a, r in rows.items() if r.status in ("open", "running")}
outcomes = JOIN.reconcile_finished_children(rows, unresolved, jobs=jobs)
for attempt, reason in sorted(outcomes.items()):
    print(f"{attempt}\t{reason}")
PY
) || { echo "FAIL: reconcile_finished_children raised"; fail=1; }
echo "$out"

blocked=$(cat "$WORK/.pre/blocked_attempt_id.txt")

# 2. HARD — the open leg's row is now `done` with note containing
#    dead-worker-blocked. A row left `open`, or closed dead-invalid-envelope,
#    fails.
blocked_line=$(grep "attempt_id=$blocked," "$WORK/jobs.log")
tab=$(printf '\t')
if ! printf '%s\n' "$blocked_line" | grep -q "${tab}done${tab}"; then
  echo "FAIL: blocked leg row is not done"; fail=1
elif ! printf '%s\n' "$blocked_line" | grep -q "note=dead-worker-blocked"; then
  echo "FAIL: blocked leg row closed without note=dead-worker-blocked"; fail=1
elif printf '%s\n' "$blocked_line" | grep -q "note=dead-invalid-envelope"; then
  echo "FAIL: blocked leg closed as dead-invalid-envelope, not typed BLOCKED (round_1 finding 1 ordering bug)"; fail=1
else
  echo "OK: blocked leg row closed done,note=dead-worker-blocked"
fi

# 3. HARD — the two sibling rows are byte-identical to $WORK/.pre/ (SD-77
#    no breadth-close).
sib_a=$(sed -n '1p' "$WORK/.pre/sibling_rows.txt")
sib_b=$(sed -n '2p' "$WORK/.pre/sibling_rows.txt")
if grep -qF "$sib_a" "$WORK/jobs.log" && grep -qF "$sib_b" "$WORK/jobs.log"; then
  echo "OK: sibling rows byte-identical (no breadth-close)"
else
  echo "FAIL: a sibling row was mutated (SD-77 breadth-close)"; fail=1
fi

# 4. HARD — a second reconcile pass leaves jobs.log byte-identical
#    (idempotent).
before_second=$(sha256sum "$WORK/jobs.log" 2>/dev/null | awk '{print $1}' || shasum -a 256 "$WORK/jobs.log" | awk '{print $1}')
AGENT_HOME="$HARNESS_ROOT" python3 - "$WORK" "$HARNESS_ROOT" <<'PY' >/dev/null
import sys
sys.path.insert(0, sys.argv[2] + "/utilities")
from pathlib import Path
import dispatch_completion_join as JOIN

work = Path(sys.argv[1])
jobs = work / "jobs.log"
parent = (work / ".pre/parent_attempt_id.txt").read_text().strip()
rows = {row.attempt_id: row for row in JOIN.current_children(jobs, parent)}
unresolved = {a for a, r in rows.items() if r.status in ("open", "running")}
JOIN.reconcile_finished_children(rows, unresolved, jobs=jobs)
PY
after_second=$(sha256sum "$WORK/jobs.log" 2>/dev/null | awk '{print $1}' || shasum -a 256 "$WORK/jobs.log" | awk '{print $1}')
if [ "$before_second" = "$after_second" ]; then
  echo "OK: second reconcile pass is a no-op (idempotent)"
else
  echo "FAIL: second reconcile pass mutated jobs.log"; fail=1
fi

# 5. HARD — no completion marker was created for the BLOCKED node under
#    .dispatch/completion/<route_id>/ (a typed failure must not manufacture
#    success, SD-72).
route_id=$(python3 -c "import json; print(json.load(open('$WORK/.runtime/routes/drill.json'))['route_id'])")
if [ -d "$HARNESS_ROOT/.dispatch/completion/$route_id" ]; then
  echo "FAIL: a completion marker exists for the BLOCKED route/node — typed failure manufactured success"; fail=1
else
  echo "OK: no completion marker created for the BLOCKED node"
fi

# 6. HARD — the supervisor loop over this fixture returns without
#    owned-children-remain-open-after-resume (fix 4 end-to-end). By this
#    point in the script the row is already closed by step 1's direct
#    reconcile call, so the equivalent supervisor-facing assertion is that
#    runtime_reconcile's own emitted outcome is `closed`, not `skipped`, for
#    the exact blocked attempt — verified by the outcomes line captured in
#    $out above.
outcome_reason=$(printf '%s\n' "$out" | awk -F'\t' -v a="$blocked" '$1==a{print $2; found=1} END{if(!found) print "MISSING"}')
if [ "$outcome_reason" = "" ]; then
  echo "OK: reconcile outcome for the blocked attempt is closed (empty reason)"
else
  echo "FAIL: reconcile outcome for the blocked attempt was not closed (reason='$outcome_reason')"; fail=1
fi

# 7. SOFT(WARN) — dispatch.supervisor.reconciled with outcome=closed appears
#    in the emitted event stream. This drill drives the join layer directly
#    (not the full supervisor CLI), so the equivalent evidence is the closed
#    outcome captured above; a full supervisor-CLI drive is out of scope for
#    a static case.
echo "WARN(soft): full supervisor CLI event stream not driven by this static case; outcomes line is the closed-evidence proxy"

exit $fail
