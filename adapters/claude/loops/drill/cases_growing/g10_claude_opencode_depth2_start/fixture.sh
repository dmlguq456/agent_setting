#!/bin/bash
# g10_claude_opencode_depth2_start: Claude depth-1 owner starts an OpenCode depth-2 worker.
set -eu
WORK=$1
REPO="$WORK/repo"
OBSERVE_SECONDS="${DRILL_G10_OBSERVE_SECONDS:-0}"
case "$OBSERVE_SECONDS" in
  ''|*[!0-9]*) OBSERVE_SECONDS=0 ;;
esac
mkdir -p "$REPO/.dispatch" "$REPO/src" "$WORK/.pre"
cd "$REPO"
git init -q && git checkout -q -b main
git config user.email drill@test && git config user.name drill
cat > README.md <<'MD'
# Claude owner to OpenCode depth-2 fixture

This fixture checks the real cross-harness start path:

- the drill parent is Claude Code (`DRILL_ADAPTER=claude`);
- the parent registers a Claude depth-1 owner row;
- the parent starts an OpenCode depth-2 child through the OpenCode dispatch wrapper;
- the child must emit the marker from `opencode_depth2_prompt.md` in its JSON log.
MD
cat > src/__init__.py <<'PY'
PY
{
cat <<'MD'
You are the OpenCode depth-2 verifier for drill case g10_claude_opencode_depth2_start.

MD
if [ "$OBSERVE_SECONDS" -gt 0 ]; then
  printf 'First run `sleep %s` so the fleet UI has time to show this depth-2 dispatch row.\n\n' "$OBSERVE_SECONDS"
fi
cat <<'MD'
Do not edit files. Reply with one short line containing exactly this marker and the parent linkage:

OPENCODE_DEPTH2_VERIFIER_PASS parent=xh-claude-owner owner_harness=claude depth=2
MD
} > opencode_depth2_prompt.md
git add -A && git commit -q -m init
printf '%s\n' "$REPO/.dispatch/jobs.log" > "$WORK/.pre/jobs_path"
