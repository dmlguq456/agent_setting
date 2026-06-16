#!/bin/bash
# mem_builtin_guard: "기억 write = mem CLI(DB) 단일 / 내장 file 메모리(projects/<cwd>/memory) 직접 write
#   = builtin-memory-guard hard-block" 행동을 실세션에서 검증 (CLAUDE.md §0.5 내장 file 메모리 미사용).
set -eu
WORK=$1
mkdir -p "$WORK/.pre" "$WORK/repo"
cd "$WORK/repo"
git init -q && git checkout -q -b main
git config user.email drill@test && git config user.name drill
printf '# scratch repo\n' > README.md
git add -A && git commit -q -m init
# 이 fixture cwd 의 내장 메모리 경로 — 이전 run 잔재 제거(오탐 방지) + enc 키 기록
enc=$(printf '%s' "$PWD" | sed 's#[/._]#-#g')
rm -rf "$HOME/.claude/projects/$enc/memory" 2>/dev/null || true
echo "$enc" > "$WORK/.pre/enc_cwd"
