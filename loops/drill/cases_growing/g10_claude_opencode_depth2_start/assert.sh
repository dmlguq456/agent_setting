#!/bin/bash
# Negative contract: OpenCode standard+ depth-2 creates no row or runtime.
set -eu
WORK=$1
REPO="$WORK/repo"
CASE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
HARNESS_ROOT=$(git -C "$CASE_DIR" rev-parse --show-toplevel)
JOBS="$REPO/.dispatch/jobs.log"
LOG_DIR="$REPO/.dispatch/logs"
SLUG="g10-opencode-depth2-blocked"
FAKE_BIN="$WORK/fake-bin"
RUNTIME_SENTINEL="$WORK/opencode-runtime-started"
GOVERNOR_ROOT="$WORK/model-worker-governor"

mkdir -p "$FAKE_BIN"
printf '%s\n' \
  '#!/bin/sh' \
  ': > "$OPENCODE_RUNTIME_SENTINEL"' \
  'exit 97' > "$FAKE_BIN/opencode"
chmod +x "$FAKE_BIN/opencode"

set +e
OUTPUT=$(PATH="$FAKE_BIN:$PATH" \
  OPENCODE_RUNTIME_SENTINEL="$RUNTIME_SENTINEL" \
  AGENT_MODEL_GOVERNOR_ROOT="$GOVERNOR_ROOT" \
  AGENT_HOME="$HARNESS_ROOT" \
  "$HARNESS_ROOT/adapters/opencode/bin/dispatch-headless.py" --start \
  --worktree "$REPO" --jobs "$JOBS" --log-dir "$LOG_DIR" \
  --slug "$SLUG" --capability autopilot-code --mode qa/test --qa standard \
  --intensity standard --dispatch-depth 2 --parent g10-owner \
  --parent-session-id g10-parent-session --worker-type review \
  --assigned-contract code-test --owner autopilot-code --owner-harness codex \
  --parent-harness codex --parent-transport headless \
  --parent-sandbox workspace-write --launch-authority conductor \
  --nested-eligibility supported --eligibility-source drill-fixture \
  --inherit-model-settings 2>&1)
RC=$?
set -e

printf '%s\n' "$OUTPUT"
[ "$RC" -eq 69 ] || { echo "FAIL: expected exit 69, got $RC"; exit 1; }
printf '%s\n' "$OUTPUT" | grep -qx 'check=failed'
printf '%s\n' "$OUTPUT" | grep -qx 'reason=opencode-standard-depth2-unsupported'
printf '%s\n' "$OUTPUT" | grep -qx 'child_spawned=0'

if [ -e "$GOVERNOR_ROOT" ]; then
  echo "FAIL: blocked OpenCode child touched governor state"
  exit 1
fi
if [ -e "$RUNTIME_SENTINEL" ]; then
  echo "FAIL: blocked OpenCode child started a runtime process"
  exit 1
fi
if [ -e "$JOBS" ]; then
  echo "FAIL: blocked OpenCode child created a registry"
  exit 1
fi
if find "$LOG_DIR" -type f -print -quit | grep -q .; then
  echo "FAIL: blocked OpenCode child wrote prompt/log material"
  exit 1
fi

PYTHONDONTWRITEBYTECODE=1 HARNESS_ROOT="$HARNESS_ROOT" JOBS="$JOBS" SLUG="$SLUG" python3 - <<'PY'
import os
import sys
from pathlib import Path

root = Path(os.environ["HARNESS_ROOT"])
sys.path.insert(0, str(root / "tools"))
from fleet.collectors import dispatch

jobs = dispatch.collect(jobs_path=os.environ["JOBS"])
assert all(job.slug != os.environ["SLUG"] for job in jobs)
print("PASS: OpenCode dispatch-depth-2 --start fails closed with zero registry/governor/runtime/prompt/log/Fleet child")
PY
