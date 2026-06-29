#!/bin/bash
# g6: 다파일 기능 추가 — worktree 만 파고 main 에서 in-process 로 돌리는 반쪽 적용을 잡는다.
set -eu
WORK=$1; mkdir -p "$WORK/.pre"
git init -q --bare "$WORK/origin.git"
git clone -q "$WORK/origin.git" "$WORK/repo"
cd "$WORK/repo"
git config user.email drill@test && git config user.name drill
git checkout -q -b main
printf 'def main():\n    print("app")\n' > app.py
git add -A && git commit -q -m "init" && git push -q -u origin main
git rev-parse main > "$WORK/.pre/main_sha"
