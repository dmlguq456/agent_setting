#!/bin/bash
# hard: selected-adapter dispatch-depth-1 owner must start an OpenCode dispatch-depth-2 worker through wrappers.
set -u
WORK=$1
T=$2
REPO="$WORK/repo"
CASE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
HARNESS_ROOT=$(git -C "$CASE_DIR" rev-parse --show-toplevel 2>/dev/null || pwd)
AGENT_HOME="${AGENT_HOME:-$HARNESS_ROOT}"
JOBS="${AGENT_DISPATCH_JOBS:-$AGENT_HOME/.dispatch/jobs.log}"
LOG_DIR="$AGENT_HOME/.dispatch/logs"
SLUGS="$REPO/.dispatch/g10_slugs.env"
WRAPPER_OUT="$REPO/dispatch_wrapper_output.txt"
PARENT_ENV="$REPO/.dispatch/g10_parent.env"
fail=0

[ -f "$PARENT_ENV" ] || { echo "FAIL: .dispatch/g10_parent.env 없음"; exit 1; }
# shellcheck source=/dev/null
. "$PARENT_ENV"
case "${PARENT_ADAPTER:-}:${PARENT_RUNTIME_SURFACE:-}" in
  claude:claude-print-headless|codex:codex-exec-headless|opencode:opencode-run-headless) ;;
  *) echo "FAIL: invalid parent adapter contract"; exit 1 ;;
esac
case "${PARENT_SESSION_ID:-}" in
  ''|*[!A-Za-z0-9_.:-]*) echo "FAIL: invalid resolved parent session id"; exit 1 ;;
esac

if [ ! -f "$SLUGS" ]; then
  echo "FAIL: .dispatch/g10_slugs.env 없음"
  exit 1
fi
# shellcheck source=/dev/null
. "$SLUGS"
: "${OWNER_SLUG:=}"
: "${CHILD_SLUG:=}"
case "$OWNER_SLUG:$CHILD_SLUG" in
  *[!A-Za-z0-9_.:-]*|:|*:)
    echo "FAIL: invalid g10 slug values OWNER_SLUG='$OWNER_SLUG' CHILD_SLUG='$CHILD_SLUG'"
    exit 1
    ;;
esac
OC_LOG="$LOG_DIR/$CHILD_SLUG.opencode.jsonl"
OC_PROMPT_COPY="$LOG_DIR/$CHILD_SLUG.opencode.prompt.txt"

[ -f "$REPO/src/slugger.py" ] || { echo "FAIL: src/slugger.py 없음"; fail=1; }
[ -f "$REPO/skill_result.md" ] || { echo "FAIL: skill_result.md 없음"; fail=1; }

PYTHONPATH="$REPO" python3 - <<'PY' || fail=1
from src.slugger import slugify

cases = {
    "  Hello, Claude Code!!  ": "hello-claude-code",
    "OpenCode___Depth 2": "opencode-depth-2",
    " already-clean ": "already-clean",
    "---Many---Separators---": "many-separators",
}
for raw, want in cases.items():
    got = slugify(raw)
    if got != want:
        raise SystemExit(f"slugify({raw!r}) -> {got!r}, want {want!r}")
print("PASS: slugify behavior")
PY

[ -f "$JOBS" ] || { echo "FAIL: .dispatch/jobs.log 없음"; exit 1; }
[ -f "$WRAPPER_OUT" ] || { echo "FAIL: dispatch_wrapper_output.txt 없음"; fail=1; }

if [ -f "$WRAPPER_OUT" ]; then
  grep -Fq "adapter=$PARENT_ADAPTER" "$WRAPPER_OUT" || { echo "FAIL: $PARENT_ADAPTER owner wrapper 출력 없음"; fail=1; }
  grep -Fq "runtime_surface=$PARENT_RUNTIME_SURFACE" "$WRAPPER_OUT" || { echo "FAIL: $PARENT_ADAPTER wrapper surface 출력 없음"; fail=1; }
  grep -q 'status=register' "$WRAPPER_OUT" || { echo "FAIL: selected owner register 출력 없음"; fail=1; }
  grep -q 'started=0' "$WRAPPER_OUT" || { echo "FAIL: selected owner는 start되면 안 됨"; fail=1; }
  grep -q 'adapter=opencode' "$WRAPPER_OUT" || { echo "FAIL: opencode child wrapper 출력 없음"; fail=1; }
  grep -q 'runtime_surface=opencode-run-headless' "$WRAPPER_OUT" || { echo "FAIL: opencode wrapper surface 출력 없음"; fail=1; }
  grep -q 'status=start' "$WRAPPER_OUT" || { echo "FAIL: opencode child start 출력 없음"; fail=1; }
  grep -q 'started=1' "$WRAPPER_OUT" || { echo "FAIL: opencode child가 start되지 않음"; fail=1; }
fi

if [ ! -f "$OC_PROMPT_COPY" ]; then
  echo "FAIL: OpenCode wrapper prompt copy 없음: $OC_PROMPT_COPY"
  fail=1
else
  grep -q 'OPENCODE_DEPTH2_VERIFIER_PASS' "$OC_PROMPT_COPY" || { echo "FAIL: OpenCode child prompt marker 누락"; fail=1; }
fi

marker="OPENCODE_DEPTH2_VERIFIER_PASS parent=$OWNER_SLUG owner_harness=$PARENT_ADAPTER dispatch_depth=2"
deadline=$((SECONDS + 240))
while [ $SECONDS -lt $deadline ]; do
  if [ -f "$OC_LOG" ] && grep -q 'OPENCODE_DEPTH2_VERIFIER_PASS' "$OC_LOG"; then
    break
  fi
  sleep 5
done
if [ ! -f "$OC_LOG" ]; then
  echo "FAIL: OpenCode child log 없음: $OC_LOG"
  fail=1
elif ! grep -q 'OPENCODE_DEPTH2_VERIFIER_PASS' "$OC_LOG"; then
  echo "FAIL: OpenCode child log에 verifier marker 없음"
  tail -80 "$OC_LOG" || true
  fail=1
elif ! grep -Fq "$marker" "$OC_LOG"; then
  echo "FAIL: OpenCode child log에 정확한 dynamic marker 없음: $marker"
  fail=1
elif ! grep -Fq "owner_harness=$PARENT_ADAPTER" "$OC_LOG"; then
  echo "FAIL: OpenCode child log에 selected owner_harness marker 없음"
  fail=1
else
  echo "PASS: OpenCode dispatch-depth-2 child emitted verifier marker"
fi

PYTHONPATH="$HARNESS_ROOT/tools" REPO="$REPO" JOBS="$JOBS" OWNER_SLUG="$OWNER_SLUG" CHILD_SLUG="$CHILD_SLUG" PARENT_ADAPTER="$PARENT_ADAPTER" PARENT_SESSION_ID="$PARENT_SESSION_ID" python3 - <<'PY' || fail=1
import os
from fleet.collectors import dispatch

repo = os.environ["REPO"]
jobs_path = os.environ["JOBS"]
owner_slug = os.environ["OWNER_SLUG"]
child_slug = os.environ["CHILD_SLUG"]
parent_adapter = os.environ["PARENT_ADAPTER"]
parent_session_id = os.environ["PARENT_SESSION_ID"]

rows = []
with open(jobs_path, encoding="utf-8") as f:
    for lineno, line in enumerate(f, 1):
        line = line.rstrip("\n")
        if not line.strip():
            continue
        fields = line.split("\t")
        if len(fields) != 6:
            continue
        ts, status, row_repo, worktree, slug, pipe = fields
        meta = {}
        for part in pipe.split(","):
            if "=" in part:
                key, value = part.split("=", 1)
                meta[key] = value
        rows.append({
            "lineno": lineno,
            "status": status,
            "repo": row_repo,
            "worktree": worktree,
            "slug": slug,
            "meta": meta,
        })

def require(condition, message):
    if not condition:
        raise SystemExit(message)

def one(slug):
    matches = [r for r in rows if r["slug"] == slug and r["worktree"] == repo]
    require(matches, f"expected at least one {slug} row for current repo, got 0")
    row = matches[-1]
    require(row["status"] in {"open", "running"}, f"{slug} latest status not live before assert harvest: {row['status']}")
    require(row["repo"] == repo, f"{slug} repo field not fixture repo: {row['repo']}")
    pipe = row["meta"]
    require(pipe and all(" " not in k and " " not in v for k, v in pipe.items()), f"{slug} metadata contains spaces: {pipe}")
    return row

def expect(row, **expected):
    meta = row["meta"]
    for key, value in expected.items():
        got = meta.get(key)
        require(got == value, f"{row['slug']} metadata {key}={got!r}, want {value!r}")

def expect_absent(row, *keys):
    for key in keys:
        require(key not in row["meta"], f"{row['slug']} legacy metadata must be absent: {key}")

def expect_attempt(row):
    attempt = row["meta"].get("attempt_id")
    require(
        bool(attempt) and attempt.startswith("att-"),
        f"{row['slug']} missing current attempt_id: {attempt!r}",
    )

owner = one(owner_slug)
expect(
    owner,
    capability="autopilot-code",
    mode="dev/refactor",
    qa="standard",
    intensity="standard",
    attempt_schema_version="2",
    dispatch_depth="1",
    transport="headless",
    execution_surface="registered-headless",
    registered_worker="1",
    fallback_hop="same-harness-headless",
    harness=parent_adapter,
    parent_sid=parent_session_id,
    worker_type="owner",
    assigned_contract="autopilot-code",
    owner="autopilot-code",
    owner_harness=parent_adapter,
    model_source="inherit",
    model_role="inherit",
    model="inherit",
)
expect_attempt(owner)
expect_absent(owner, "worker_role")

child = one(child_slug)
child_hop = (
    "same-harness-headless"
    if parent_adapter == "opencode"
    else "cross-harness-headless"
)
expect(
    child,
    capability="code-test",
    mode="qa/test",
    qa="standard",
    intensity="standard",
    attempt_schema_version="2",
    dispatch_depth="2",
    transport="headless",
    execution_surface="registered-headless",
    registered_worker="1",
    fallback_hop=child_hop,
    harness="opencode",
    parent=owner_slug,
    parent_sid=parent_session_id,
    worker_type="review",
    assigned_contract="code-test",
    owner="autopilot-code",
    owner_harness=parent_adapter,
    model_source="inherit",
    model_role="inherit",
    model="inherit",
    variant="inherit",
)
expect_attempt(child)
expect_absent(child, "worker_role")

jobs = dispatch.collect(jobs_path=jobs_path)
fleet_owner = [
    j for j in jobs
    if j.slug == owner_slug
    and j.key == "code"
    and j.mode == "dev/refactor"
    and j.depth == 1
    and j.harness == parent_adapter
    and j.worker_type == "owner"
    and j.assigned_contract == "autopilot-code"
    and j.capability_owner == "autopilot-code"
    and j.parent_sid == parent_session_id
]
fleet_child = [
    j for j in jobs
    if j.slug == child_slug
    and j.parent_slug == owner_slug
    and j.depth == 2
    and j.harness == "opencode"
    and j.is_child
    and j.parent_sid == parent_session_id
    and j.capability_owner == "autopilot-code"
    and j.worker_type == "review"
    and j.assigned_contract == "code-test"
    and j.worker_role is None
]
require(fleet_owner, f"fleet parse missing {parent_adapter} dispatch-depth-1 owner")
require(fleet_child, f"fleet parse missing OpenCode dispatch-depth-2 child linked to {parent_adapter} owner")
print(f"PASS: fleet collector preserves {parent_adapter} dispatch-depth-1 -> OpenCode dispatch-depth-2 linkage")
PY

if [ "$fail" -eq 0 ]; then
  "$AGENT_HOME/adapters/opencode/bin/preflight.sh" harvest --jobs "$JOBS" --slug "$OWNER_SLUG" --mark-done >/dev/null 2>&1 || true
  "$AGENT_HOME/adapters/opencode/bin/preflight.sh" harvest --jobs "$JOBS" --slug "$CHILD_SLUG" --mark-done >/dev/null 2>&1 || true
fi

exit $fail
