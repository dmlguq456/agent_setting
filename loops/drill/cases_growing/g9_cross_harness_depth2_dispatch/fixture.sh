#!/bin/bash
# g9_cross_harness_depth2_dispatch: registry shape for depth-2 cross-harness dispatch.
set -eu
WORK=$1
REPO="$WORK/repo"
mkdir -p "$REPO/.dispatch" "$WORK/.pre"
cd "$REPO"
git init -q && git checkout -q -b main
git config user.email drill@test && git config user.name drill
cat > README.md <<'MD'
# Cross-harness depth-2 dispatch fixture

This fixture is intentionally local-only. Do not launch real headless sessions.
Write the modeled dispatch registry to `.dispatch/jobs.log` using the portable 6-field format:

`<ISO>\t<status>\t<repo>\t<worktree>\t<slug>\t<pipe metadata>`
MD
git add -A && git commit -q -m init
printf '%s\n' "$REPO/.dispatch/jobs.log" > "$WORK/.pre/jobs_path"
