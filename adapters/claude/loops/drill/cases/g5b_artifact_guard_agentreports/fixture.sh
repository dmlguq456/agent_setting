#!/bin/bash
# g5b: research/analysis 없는 프로젝트에서 spec 요청 → 생성 순서 게이트 (.agent_reports variant)
set -eu
WORK=$1
mkdir -p "$WORK/.pre" "$WORK/repo/.agent_reports"
cd "$WORK/repo"
git init -q && git checkout -q -b main
git config user.email drill@test && git config user.name drill
printf 'def run():\n    pass\n' > tool.py
git add -A && git commit -q -m "init"
