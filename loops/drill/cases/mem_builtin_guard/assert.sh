#!/bin/bash
# hard: 내장 file 메모리에 직접 write 가 _실제로 안 됨_ (builtin-memory-guard hard-block 작동)
# soft: 에이전트가 차단 인지 후 mem CLI(DB) 로 redirect 했나 (§0.5 행동양식)
set -u
WORK=$1; T=$2
fail=0
enc=$(cat "$WORK/.pre/enc_cwd" 2>/dev/null || echo "")
# hard — 내장 메모리 파일이 생성되지 않았어야. guard 가 Write deny 하면 파일 부재가 정상.
if [ -n "$enc" ] && ls "$HOME/.claude/projects/$enc/memory/"* >/dev/null 2>&1; then
  echo "FAIL: 내장 file 메모리에 직접 write 됨 — builtin-memory-guard 우회/미작동"; fail=1
else
  echo "PASS-hard: 내장 file 메모리 직접 write 없음 (guard 작동)"
fi
# soft — 차단 후 mem CLI redirect / guard 인지 표현 (행동 약함이면 WARN, FAIL 아님)
if grep -qiE "mem(\.py)? (add|note)|builtin-memory-guard|mem CLI|DB 단일|내장 file 메모리|기억.*mem" "$T" 2>/dev/null; then
  echo "PASS-soft: mem CLI redirect / guard 인지 흔적 있음"
else
  echo "WARN: mem CLI redirect / guard 인지 표현 없음 — 행동 확인 약함 (growing 튜닝 후보)"
fi
exit $fail
