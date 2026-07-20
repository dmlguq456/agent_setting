#!/bin/bash
# g9_cross_harness_depth2_dispatch: autopilot-code should register dispatch-depth-2 cross-harness work.
set -eu
WORK=$1
REPO="$WORK/repo"
mkdir -p "$REPO/.dispatch" "$REPO/src" "$WORK/.pre"
cd "$REPO"
git init -q && git checkout -q -b main
git config user.email drill@test && git config user.name drill
cat > README.md <<'MD'
# Cross-harness dispatch-depth-2 fixture

This fixture is intentionally local-only. Do not launch real headless sessions.
Use adapter dispatch wrappers with `--register` to append the portable 6-field jobs.log rows:

`<ISO>\t<status>\t<repo>\t<worktree>\t<slug>\t<pipe metadata>`

Do not hand-write `.dispatch/jobs.log`. The skill should register:

- one Codex dispatch-depth-1 `autopilot-code` owner named `xh-depth2-owner`;
- one Claude dispatch-depth-2 child under that owner;
- one OpenCode dispatch-depth-2 child under that owner.
MD
cat > src/__init__.py <<'PY'
PY
git add -A && git commit -q -m init
printf '%s\n' "$REPO/.dispatch/jobs.log" > "$WORK/.pre/jobs_path"
