#!/bin/bash
# g12_profile_home_credentials: a build-home instance must project the runtime
# credential into the masked home. Regression anchor: 2026-07-19 r1b — profiled
# claude children spawned logged-out (note=dead-auth) because the credential
# source pointed at the repo root instead of the runtime home (fixed f9aba396).
set -eu
WORK=$1
REPO="$WORK/repo"
mkdir -p "$REPO/.dispatch" "$WORK/.pre"
cd "$REPO"
git init -q && git checkout -q -b main
git config user.email drill@test && git config user.name drill
cat > README.md <<'MD'
# Profile-home credential projection fixture

Local-only. Build a masked profile home with build-home.py and verify the
credential SYMLINK is projected (`.credentials.json` → an existing runtime
file). Never read or print credential CONTENTS — link presence and target
existence only. Do not start any headless runtime.
MD
git add -A && git commit -q -m init
