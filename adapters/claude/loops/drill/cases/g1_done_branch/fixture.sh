#!/bin/bash
# g1: 머지 완료된 죽은 브랜치에 checkout 된 상태
set -eu
WORK=$1
mkdir -p "$WORK/.pre"
git init -q --bare "$WORK/origin.git"
git clone -q "$WORK/origin.git" "$WORK/repo"
cd "$WORK/repo"
git config user.email drill@test && git config user.name drill
git checkout -q -b main
printf 'def add(a, b):\n    return a + b\n' > calc.py
git add -A && git commit -q -m "init" && git push -q -u origin main
# feature 브랜치 → 작업 → main 에 머지 → push (= 끝난 브랜치)
git checkout -q -b feature/old-task
printf 'def helper():\n    return 1\n' > utils.py
git add -A && git commit -q -m "feat: helper"
git checkout -q main && git merge -q --no-ff feature/old-task -m "merge old-task" && git push -q origin main
git checkout -q feature/old-task   # 죽은 브랜치에 머묾 (ahead 0)
git rev-parse feature/old-task > "$WORK/.pre/feature_sha"
git rev-parse main > "$WORK/.pre/main_sha"
