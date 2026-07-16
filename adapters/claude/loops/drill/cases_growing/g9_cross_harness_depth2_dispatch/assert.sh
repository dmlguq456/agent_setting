#!/bin/bash
# hard: autopilot-code must use dispatch wrappers to register depth-2 cross-harness workers.
set -u
WORK=$1
T=$2
REPO="$WORK/repo"
JOBS="$REPO/.dispatch/jobs.log"
fail=0

[ -f "$REPO/src/normalizer.py" ] || { echo "FAIL: src/normalizer.py 없음"; fail=1; }
[ -f "$REPO/skill_result.md" ] || { echo "FAIL: skill_result.md 없음"; fail=1; }

PYTHONPATH="$REPO" python3 - <<'PY' || fail=1
from src.normalizer import normalize_name

cases = {
    "  Alice   BOB\tKim  ": "alice bob kim",
    "ONE\n\nTwo": "one two",
    " already-clean ": "already-clean",
}
for raw, want in cases.items():
    got = normalize_name(raw)
    if got != want:
        raise SystemExit(f"normalize_name({raw!r}) -> {got!r}, want {want!r}")
print("PASS: normalize_name behavior")
PY

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

if awk -F '\t' 'NF == 6 && ($6 ~ / / || $6 !~ /,/ || $6 !~ /=/) {bad=1} END {exit bad ? 0 : 1}' "$JOBS"; then
  echo "FAIL: pipe metadata는 공백 없는 comma-separated key=value 여야 함"
  fail=1
fi

RAW="${T%.transcript.txt}.json"
if [ ! -f "$RAW" ]; then
  echo "FAIL: raw codex json transcript 없음: $RAW"
  fail=1
else
  grep -q 'adapter=codex' "$RAW" || { echo "FAIL: codex dispatch wrapper 출력 없음"; fail=1; }
  grep -q 'runtime_surface=codex-exec-headless' "$RAW" || { echo "FAIL: codex dispatch wrapper surface 출력 없음"; fail=1; }
  grep -q 'adapter=claude' "$RAW" || { echo "FAIL: claude dispatch wrapper 출력 없음"; fail=1; }
  grep -q 'runtime_surface=claude-print-headless' "$RAW" || { echo "FAIL: claude dispatch wrapper surface 출력 없음"; fail=1; }
  grep -q 'adapter=opencode' "$RAW" || { echo "FAIL: opencode dispatch wrapper 출력 없음"; fail=1; }
  grep -q 'runtime_surface=opencode-run-headless' "$RAW" || { echo "FAIL: opencode dispatch wrapper surface 출력 없음"; fail=1; }
  register_count=$(grep -o 'status=register' "$RAW" | wc -l | tr -d ' ')
  started_zero_count=$(grep -o 'started=0' "$RAW" | wc -l | tr -d ' ')
  [ "${register_count:-0}" -ge 3 ] || { echo "FAIL: wrapper register 출력 3개 미만: $register_count"; fail=1; }
  [ "${started_zero_count:-0}" -ge 3 ] || { echo "FAIL: --register run should not start runtimes; started=0 3개 미만: $started_zero_count"; fail=1; }
fi

CASE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
HARNESS_ROOT=$(git -C "$CASE_DIR" rev-parse --show-toplevel 2>/dev/null || pwd)
PYTHONPATH="$HARNESS_ROOT/tools" REPO="$REPO" JOBS="$JOBS" python3 - <<'PY' || fail=1
import os
import re
from fleet.collectors import dispatch

repo = os.environ["REPO"]
jobs_path = os.environ["JOBS"]

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
    matches = [r for r in rows if r["slug"] == slug]
    require(len(matches) == 1, f"expected exactly one {slug} row, got {len(matches)}")
    return matches[0]

def expect(row, **expected):
    meta = row["meta"]
    for key, value in expected.items():
        got = meta.get(key)
        require(got == value, f"{row['slug']} metadata {key}={got!r}, want {value!r}")

require(len(rows) >= 3, f"expected at least 3 wrapper rows, got {len(rows)}")
for row in rows:
    require(row["status"] in {"open", "running"}, f"{row['slug']} not live status: {row['status']}")
    require(row["repo"] == repo, f"{row['slug']} repo field not fixture repo: {row['repo']}")
    require(row["worktree"] == repo, f"{row['slug']} worktree field not fixture repo: {row['worktree']}")
    require(row["meta"].get("model_source") == "explicit", f"{row['slug']} missing wrapper explicit model metadata")

owner = one("xh-depth2-owner")
expect(
    owner,
    capability="autopilot-code",
    mode="dev/refactor",
    qa="standard",
    intensity="thorough",
    depth="1",
    harness="codex",
    worker_role="capability-owner",
    owner="autopilot-code",
    owner_harness="codex",
    model="gpt-5.4-mini",
    reasoning="medium",
)
# Owner is depth-1 and gets rebound to the real Codex thread id at launch, so it
# is checked only for a well-formed SID (best-effort match, not exact equality);
# both depth-2 children still assert exact drill-parent-session below.
owner_sid = owner["meta"].get("parent_sid")
require(
    bool(owner_sid) and re.fullmatch(r"[A-Za-z0-9_.:-]+", owner_sid or ""),
    f"xh-depth2-owner parent_sid not a well-formed SID: {owner_sid!r}",
)

claude = one("xh-depth2-claude-verifier")
expect(
    claude,
    capability="code-test",
    mode="qa/test",
    qa="standard",
    intensity="thorough",
    depth="2",
    harness="claude",
    parent="xh-depth2-owner",
    parent_sid="drill-parent-session",
    worker_role="verifier",
    owner="autopilot-code",
    owner_harness="codex",
    model="sonnet",
    effort="medium",
)

opencode = one("xh-depth2-opencode-plan-review")
expect(
    opencode,
    capability="code-plan",
    mode="qa/plan-review",
    qa="standard",
    intensity="thorough",
    depth="2",
    harness="opencode",
    parent="xh-depth2-owner",
    parent_sid="drill-parent-session",
    worker_role="planner",
    owner="autopilot-code",
    owner_harness="codex",
    model="opencode/test",
    variant="low",
)

jobs = dispatch.collect(jobs_path=jobs_path)
fleet_owner = [
    j for j in jobs
    if j.slug == "xh-depth2-owner"
    and j.key == "code"
    and j.mode == "dev/refactor"
    and j.depth == 1
    and j.harness == "codex"
    and j.worker_role == "capability-owner"
    and j.capability_owner == "autopilot-code"
    and j.parent_sid and re.fullmatch(r"[A-Za-z0-9_.:-]+", j.parent_sid)
]
children = [j for j in jobs if j.parent_slug == "xh-depth2-owner" and j.depth == 2]
harnesses = {j.harness for j in children}
require(fleet_owner, "fleet parse missing autopilot-code codex depth-1 owner")
require({"claude", "opencode"}.issubset(harnesses), f"fleet parse missing cross-harness depth2 children: {sorted(harnesses)}")
require(all(j.is_child for j in children), "fleet parse did not mark depth2 children as child jobs")
require(all(j.parent_sid == "drill-parent-session" for j in children), "fleet parse lost parent session linkage")
print("PASS: wrapper rows and fleet collector preserve depth-1/depth-2 cross-harness linkage")
PY

exit $fail
