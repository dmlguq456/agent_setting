#!/bin/bash
# g_stage_dispatch_blocked_leg: a BLOCKED codex leg leaves an open row and the
# owner must recover (dispatch-guard-identity cycle, fixes 3+4, plan.md §7).
# AXIS=static — this proves the harness can deterministically recover, not
# that the model elects to; see prompt.md.
set -eu
WORK=$1
CASE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
HARNESS_ROOT=$(CDPATH= cd -- "$CASE_DIR/../../../.." && pwd)
mkdir -p "$WORK/.pre" "$WORK/.runtime/routes"

# 1. spec-backed repo fixture.
git init -q "$WORK/repo"
cd "$WORK/repo"
git config user.email drill@test && git config user.name drill
mkdir -p .agent_reports/spec/stage-dispatch
cat > .agent_reports/spec/stage-dispatch/prd.md <<'PRD'
# PRD — stage-dispatch (drill fixture)

Fixture-only governing spec for g_stage_dispatch_blocked_leg.
PRD
printf 'x = 1\n' > x.py
git add -A && git commit -q -m "init: spec-backed fixture"

# 2. compile a real tracked route bound to $WORK/repo.
python3 - "$WORK" "$HARNESS_ROOT" <<'PY'
import importlib.util, json, sys
from pathlib import Path

work = Path(sys.argv[1])
harness_root = Path(sys.argv[2])
repo = work / "repo"
artifact_root = repo / ".agent_reports"

spec = importlib.util.spec_from_file_location(
    "capability_route_drill", harness_root / "utilities" / "capability-route.py"
)
ROUTE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ROUTE)

gate = {
    "spec_read": {"satisfied": True, "source": "fixture"},
    "drift_verdict": "within-spec",
    "workflow_mode": "tracked",
    "artifact_guard": {"satisfied": True, "source": "fixture"},
}
dispatch_evidence = {
    "tuples": [{
        "parent_harness": "codex", "parent_transport": "headless",
        "parent_sandbox": "workspace-write", "child_harness": "codex",
        "launch_authority": "conductor", "status": "supported",
        "probe_source": "fixture", "probe_time": "2026-08-05T00:00:00Z",
        "failure_class": "",
    }],
    "native_subagent": [],
}
route = ROUTE.compile_route(
    "autopilot-code", "dev", "strong", repo, artifact_root,
    signals=["shared-contract"], transport="headless",
    tracking="tracked", tracked_gate_evidence=gate,
    dispatch_evidence=dispatch_evidence,
)
(work / ".runtime/routes/drill.json").write_text(json.dumps(route), encoding="utf-8")
node = next(n for n in route["nodes"] if n["id"] == "frame")
(work / ".pre/route_node.txt").write_text(node["id"], encoding="utf-8")
PY

route_id=$(python3 -c "import json; print(json.load(open('$WORK/.runtime/routes/drill.json'))['route_id'])")
route_hash=$(python3 -c "import json; print(json.load(open('$WORK/.runtime/routes/drill.json'))['route_hash'])")

# 3. leg's exact attempt log — the observed incident's byte shape.
cat > "$WORK/leg.codex.jsonl" <<EOF
{"type":"system","subtype":"init"}
{"type":"item.completed","item":{"type":"agent_message","text":"artifact: -\nverdict: BLOCKED\nblocker: guard-identity-unavailable"}}
{"type":"turn.completed"}
EOF

# 4. jobs.log — two done siblings + one open BLOCKED depth-2 codex leg.
parent="att-parent-drill"
sib_a="att-sibling-a"
sib_b="att-sibling-b"
blocked="att-blocked-leg"

row_a="2026-08-05T00:00:00Z	done	$WORK/repo	$WORK/repo	sibling-a	attempt_schema_version=2,dispatch_depth=2,transport=headless,execution_surface=registered-headless,registered_worker=1,fallback_hop=same-harness-headless,harness=codex,attempt_id=$sib_a,parent_attempt_id=$parent,note=completed-marker"
row_b="2026-08-05T00:00:00Z	done	$WORK/repo	$WORK/repo	sibling-b	attempt_schema_version=2,dispatch_depth=2,transport=headless,execution_surface=registered-headless,registered_worker=1,fallback_hop=same-harness-headless,harness=codex,attempt_id=$sib_b,parent_attempt_id=$parent,note=completed-marker"
row_blocked="2026-08-05T00:00:00Z	open	$WORK/repo	$WORK/repo	blocked-leg	attempt_schema_version=2,dispatch_depth=2,transport=headless,execution_surface=registered-headless,registered_worker=1,fallback_hop=same-harness-headless,harness=codex,attempt_id=$blocked,parent_attempt_id=$parent,route_id=$route_id,route_hash=$route_hash,route_node=frame,route_file=$WORK/.runtime/routes/drill.json,log_file=$WORK/leg.codex.jsonl,artifact_root=$WORK/repo/.agent_reports,launch_outcome=reaped-before-publish"

printf '%s\n%s\n%s\n' "$row_a" "$row_b" "$row_blocked" > "$WORK/jobs.log"

# 5. pre-state snapshot for the no-mutation / idempotence assertions.
mkdir -p "$WORK/.pre"
printf '%s\n%s\n' "$row_a" "$row_b" > "$WORK/.pre/sibling_rows.txt"
sha256sum "$WORK/jobs.log" > "$WORK/.pre/jobs.sha256" 2>/dev/null \
  || shasum -a 256 "$WORK/jobs.log" > "$WORK/.pre/jobs.sha256"
printf '%s\n' "$parent" > "$WORK/.pre/parent_attempt_id.txt"
printf '%s\n' "$blocked" > "$WORK/.pre/blocked_attempt_id.txt"
