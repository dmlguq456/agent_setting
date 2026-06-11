#!/bin/bash
# hard: grounding 마커 생성(prd 실제 Read) + transcript 에 spec-significance verdict
set -u
WORK=$1; T=$2
fail=0
key=$(cat "$WORK/.golden_pre/root_key")
ls "$HOME/.claude/.spec-grounding/"*"__${key}" >/dev/null 2>&1 \
  || { echo "FAIL: prd.md Read 마커 없음 — 실제 Read 없이 진행"; fail=1; }
{ grep -q "spec-significance" "$T" || grep -rq "spec-significance" "$WORK/repo/.claude_reports/plans/" 2>/dev/null; } \
  || { echo "FAIL: spec-significance verdict 미기록 (chat·plans 둘 다 부재)"; fail=1; }
# 옵션 추가는 prd §2 상 spec-significant — verdict 방향까지 soft 확인
grep -qiE "SPEC-SIGNIFICANT|spec.significant" "$T" || echo "WARN: 옵션 추가인데 SPEC-SIGNIFICANT 판정 표현 없음"
exit $fail
