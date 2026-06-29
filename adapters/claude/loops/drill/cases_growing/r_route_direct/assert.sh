#!/bin/bash
# r_route_direct assert
# 검증: typo·1줄급은 autopilot 파이프 안 태우고 직접 고치는가 (과잉 ceremony 회귀, CLAUDE §0(C)).
# hard: ① typo 수정됨(receive) ② 파이프 산출물(plans/spec/documents) 생성 0.
WORK="$1"; T="$2"; REPO="$WORK/repo"; fail=0
if grep -q 'receive' "$REPO/util.py" 2>/dev/null && ! grep -q 'recieve' "$REPO/util.py" 2>/dev/null; then
  echo "PASS: typo 수정됨 (recieve→receive)"
else
  echo "FAIL: typo 안 고쳐짐"; fail=1
fi
extra=$(find "$REPO/.claude_reports/plans" "$REPO/.claude_reports/spec" "$REPO/.claude_reports/documents" -type f 2>/dev/null | head -1)
if [ -z "$extra" ]; then
  echo "PASS: 파이프 산출물 0 (typo 에 과잉 ceremony 안 탐)"
else
  echo "FAIL: typo 1줄에 파이프 산출물 생성 ($extra) — 과잉 라우팅"; fail=1
fi
exit $fail
