#!/bin/bash
# g_stage_dispatch_blocked_leg — a BLOCKED codex leg leaves an open row and the
# owner must recover, exactly once, without breadth-close (fixes 3+4, plan.md
# §7). AXIS=static: no model turn ran; this drives the real supervisor
# owner-restoration entry point (`runtime_reconcile` in
# `claude-session-supervisor.py` — the exact function main()'s resume loop
# calls before ever raising `owned-children-remain-open-after-resume`), not a
# reimplementation and not a lower-level proxy.
set -u
WORK=$1; T=$2
CASE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
HARNESS_ROOT=$(CDPATH= cd -- "$CASE_DIR/../../../.." && pwd)
fail=0

# 1. Run the real owner-restoration entry point — runtime_reconcile, the
#    function the supervisor's `main()` resume loop calls before it would
#    otherwise raise owned-children-remain-open-after-resume. Not
#    reconcile_finished_children directly (that was the pre-fix proxy this
#    case used to call) and not a reimplementation.
out=$(AGENT_HOME="$HARNESS_ROOT" python3 - "$WORK" "$HARNESS_ROOT" <<'PY'
import argparse
import importlib.util
import sys
from pathlib import Path

work = Path(sys.argv[1])
harness_root = Path(sys.argv[2])
sys.path.insert(0, str(harness_root / "utilities"))

spec = importlib.util.spec_from_file_location(
    "claude_session_supervisor_drill", harness_root / "utilities" / "claude-session-supervisor.py"
)
SUP = importlib.util.module_from_spec(spec)
spec.loader.exec_module(SUP)
JOIN = sys.modules["dispatch_completion_join"]

jobs = work / "jobs.log"
parent = (work / ".pre/parent_attempt_id.txt").read_text().strip()
args = argparse.Namespace(jobs=jobs, parent_attempt_id=parent)
rows = {row.attempt_id: row for row in JOIN.current_children(jobs, parent)}
unresolved = {a for a, r in rows.items() if r.status in ("open", "running")}
closed = SUP.runtime_reconcile(args, rows, unresolved)
for attempt in sorted(closed):
    print(f"closed\t{attempt}")
for attempt in sorted(unresolved - closed):
    print(f"still-open\t{attempt}")
PY
) || { echo "FAIL: runtime_reconcile raised"; fail=1; }
events="$out"
data_lines=$(printf '%s\n' "$out" | grep -v '^{')
echo "$data_lines"

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

# 4. HARD — a second runtime_reconcile pass leaves jobs.log byte-identical
#    (idempotent) and closes nothing further.
before_second=$(sha256sum "$WORK/jobs.log" 2>/dev/null | awk '{print $1}' || shasum -a 256 "$WORK/jobs.log" | awk '{print $1}')
second_out=$(AGENT_HOME="$HARNESS_ROOT" python3 - "$WORK" "$HARNESS_ROOT" <<'PY'
import argparse
import importlib.util
import sys
from pathlib import Path

work = Path(sys.argv[1])
harness_root = Path(sys.argv[2])
sys.path.insert(0, str(harness_root / "utilities"))

spec = importlib.util.spec_from_file_location(
    "claude_session_supervisor_drill2", harness_root / "utilities" / "claude-session-supervisor.py"
)
SUP = importlib.util.module_from_spec(spec)
spec.loader.exec_module(SUP)
JOIN = sys.modules["dispatch_completion_join"]

jobs = work / "jobs.log"
parent = (work / ".pre/parent_attempt_id.txt").read_text().strip()
args = argparse.Namespace(jobs=jobs, parent_attempt_id=parent)
rows = {row.attempt_id: row for row in JOIN.current_children(jobs, parent)}
unresolved = {a for a, r in rows.items() if r.status in ("open", "running")}
closed = SUP.runtime_reconcile(args, rows, unresolved)
for attempt in sorted(closed):
    print(f"closed\t{attempt}")
PY
)
after_second=$(sha256sum "$WORK/jobs.log" 2>/dev/null | awk '{print $1}' || shasum -a 256 "$WORK/jobs.log" | awk '{print $1}')
if [ "$before_second" = "$after_second" ] && [ -z "$(printf '%s\n' "$second_out" | grep -v '^{')" ]; then
  echo "OK: second reconcile pass is a no-op (idempotent, closes nothing further)"
else
  echo "FAIL: second reconcile pass mutated jobs.log or closed another row"; fail=1
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

# 6. HARD — the owner-restoration entry point closes the blocked attempt
#    (fix 4 end-to-end): runtime_reconcile's own return value names it
#    closed, which is exactly the condition that lets main()'s resume loop
#    continue instead of raising owned-children-remain-open-after-resume.
if printf '%s\n' "$data_lines" | grep -q "^closed${tab}${blocked}\$"; then
  echo "OK: runtime_reconcile (the real owner-restoration entry point) closed the blocked attempt"
else
  echo "FAIL: runtime_reconcile did not report the blocked attempt as closed"; fail=1
fi
if printf '%s\n' "$data_lines" | grep -q "^still-open${tab}"; then
  echo "FAIL: an attempt remained open after runtime_reconcile — main() would raise owned-children-remain-open-after-resume"; fail=1
fi

# 7. HARD — the real emitted event stream (not a proxy) carries
#    dispatch.supervisor.reconciled with outcome=closed for the exact
#    blocked attempt. This step used to be a soft WARN because the case only
#    drove reconcile_finished_children, which emits nothing; runtime_reconcile
#    is the emitting layer, so this is now a real assertion.
if printf '%s\n' "$events" | grep -F "\"type\":\"dispatch.supervisor.reconciled\"" \
    | grep -F "\"attempt_id\":\"$blocked\"" | grep -qF "\"outcome\":\"closed\""; then
  echo "OK: dispatch.supervisor.reconciled outcome=closed emitted for the blocked attempt"
else
  echo "FAIL: dispatch.supervisor.reconciled outcome=closed was not emitted for the blocked attempt"; fail=1
fi

exit $fail
