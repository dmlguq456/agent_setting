#!/bin/bash
# g7 static-assert: skill-design 정량 규범(CONVENTIONS §5.6a) 회귀 게이트 (SD-4).
# 양 Claude skill 트리의 구조 + invocation 분류 계약을 실제로 강제한다.
# 사용자 turn 없음 (config AXIS=static) — run.sh 가 adapter 실행을 건너뛰고 이 assert 만 돈다.
set -u
WORK=$1
# ROOT = harness repo root (root/adapters mirror 어느 경로에서 실행해도 동일).
ROOT=$(git -C "$(dirname -- "$0")" rev-parse --show-toplevel 2>/dev/null) || exit 1
cd "$ROOT" || { echo "FAIL: repo root 해석 실패 ($ROOT)"; exit 1; }
[ -x tools/skill-conformance/check.sh ] || { echo "FAIL: tools/skill-conformance/check.sh 부재/비실행"; exit 1; }
fail=0

if out=$(bash tools/skill-conformance/check.sh skills adapters/claude/skills 2>&1); then
  echo "$out"
else
  echo "$out"
  fail=1
fi

# Checker self-test: a forbidden parent flip and a missing user-only flag must
# both fail, while an explicitly classified user-only skill with the flag passes.
if SKILL_INVOCATION_POLICY="$WORK/parent-policy.tsv" \
   bash tools/skill-conformance/check.sh "$WORK/broken-parent" >/dev/null 2>&1; then
  echo "FAIL: negative control accepted parent-invoked disable_model=true"
  fail=1
else
  echo "PASS: negative control rejected parent-invoked disable_model=true"
fi
if SKILL_INVOCATION_POLICY="$WORK/user-policy.tsv" \
   bash tools/skill-conformance/check.sh "$WORK/broken-user" >/dev/null 2>&1; then
  echo "FAIL: negative control accepted user-only disable_model=false"
  fail=1
else
  echo "PASS: negative control rejected user-only disable_model=false"
fi
if SKILL_INVOCATION_POLICY="$WORK/user-policy.tsv" \
   bash tools/skill-conformance/check.sh "$WORK/good-user" >/dev/null 2>&1; then
  echo "PASS: positive control accepted user-only disable_model=true"
else
  echo "FAIL: positive control rejected user-only disable_model=true"
  fail=1
fi

[ "$fail" = 0 ] && echo "PASS: g7 invocation 계약과 구조 규범 강제 완료"
exit $fail
