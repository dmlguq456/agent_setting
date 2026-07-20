#!/bin/bash
# g11_nested_sandbox_lifetime: a wrapper --start inside a per-call PID-namespace
# sandbox must REFUSE with the typed reason instead of spawning a doomed child.
# Regression anchor: 2026-07-20 memory-oncall-promotion-plan r1~r3 — three codex
# depth-2 workers silently SIGKILLed the moment the launcher tool call returned.
set -eu
WORK=$1
REPO="$WORK/repo"
mkdir -p "$REPO/.dispatch/logs" "$WORK/.pre"
cd "$REPO"
git init -q && git checkout -q -b main
git config user.email drill@test && git config user.name drill
cat > README.md <<'MD'
# Nested-sandbox lifetime refusal fixture

Local-only. Never start a REAL headless runtime here: every wrapper `--start`
in this drill runs inside `unshare -Urpf --mount-proc`, where the guard must
refuse BEFORE any child is spawned (`reason=nested-sandbox-lifetime`, exit 77,
registry `note=dead-nested-sandbox-lifetime`). If a run ever reaches
`started=1` the guard has regressed and the case must FAIL.
MD
git add -A && git commit -q -m init
printf '%s\n' "$REPO/.dispatch/jobs.log" > "$WORK/.pre/jobs_path"
