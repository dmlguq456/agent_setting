#!/bin/bash
# g11_nested_sandbox_lifetime: wrappers must promote a provisional detached
# selection before registration when their actual scope is transient.
# Regression anchor: 2026-07-20 memory-oncall-promotion-plan r1~r3 — three codex
# dispatch-depth-2 workers silently SIGKILLed the moment the launcher tool call returned.
set -eu
WORK=$1
REPO="$WORK/repo"
mkdir -p "$REPO/.dispatch/logs" "$WORK/.pre"
cd "$REPO"
git init -q && git checkout -q -b main
git config user.email drill@test && git config user.name drill
cat > README.md <<'MD'
# Nested-sandbox lifecycle reselection fixture

Local-only. The drill runs deterministic wrapper integration tests with fake
runtime binaries. An incoming `detached` choice must become
`foreground-scoped` before attempt registration, complete under supervision,
and expose zero `dead-nested-sandbox-lifetime` failures.
MD
git add -A && git commit -q -m init
printf '%s\n' "$REPO/.dispatch/jobs.log" > "$WORK/.pre/jobs_path"
