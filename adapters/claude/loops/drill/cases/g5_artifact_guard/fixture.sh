#!/bin/bash
# g5: research/analysis 없는 프로젝트에서 spec 요청 → 생성 순서 게이트
set -eu
WORK=$1
mkdir -p "$WORK/.pre" "$WORK/repo/.claude_reports"
cd "$WORK/repo"
git init -q && git checkout -q -b main
git config user.email drill@test && git config user.name drill
printf 'def run():\n    pass\n' > tool.py
git add -A && git commit -q -m "init"
