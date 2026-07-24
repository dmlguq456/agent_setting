#!/bin/bash
# Legacy case id, current contract: OpenCode registered depth-2 fails closed.
set -eu
WORK=$1
REPO="$WORK/repo"
mkdir -p "$REPO/.dispatch/logs"
cd "$REPO"
git init -q
git checkout -q -b main
git config user.email drill@test
git config user.name drill
printf '# OpenCode dispatch-depth-2 fail-closed fixture\n' > README.md
git add README.md
git commit -q -m init
