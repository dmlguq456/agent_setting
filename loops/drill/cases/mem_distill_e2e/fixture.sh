#!/bin/bash
# mem_distill_e2e: 자동증류 파이프라인 실배선 e2e — dispatch(argument 모드) → worker 분사 →
#   격리 MEM_STORE 에 레코드 + marker 전진. 2026-07-03 migration 파손(worker 경로·PROJECTS
#   transcript 해석이 조용히 no-op) 재발 방지 회귀 케이스. 판정은 assert.sh 가 수행.
set -eu
WORK=$1
mkdir -p "$WORK/.pre" "$WORK/repo"
cd "$WORK/repo"
git init -q && git checkout -q -b main
git config user.email drill@test && git config user.name drill
printf '# scratch repo\n' > README.md
git add -A && git commit -q -m init
# 이 fixture cwd 의 claude 세션 레지스트리 키 기록 (+ 이전 잔재 제거 — 오탐 방지)
enc=$(printf '%s' "$PWD" | sed 's#[/._]#-#g')
rm -rf "$HOME/.claude/projects/$enc" 2>/dev/null || true
echo "$enc" > "$WORK/.pre/enc_cwd"
