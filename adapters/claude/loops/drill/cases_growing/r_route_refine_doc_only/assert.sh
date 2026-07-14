#!/bin/bash
# r_route_refine_doc_only assert — WORKFLOW §0.2 Case B.
# 검증 행동: 문서 표면 수정 요청에 refine 이 primary 로 처리되고 lab 이 미선택되는가.
# HARD:
#   1. REPORT.md 오탈자 수정됨 (Summery/modle/Recieve/compair 소거).
#   2. 새 experiments 디렉토리·새 metrics 미생성 (lab 미선택).
#   3. RUNLOG 행 수 불변 (재평가 행 추가 금지).
set -u
WORK="$1"; T="$2"; fail=0

report=$(find "$WORK" -path '*/.agent_reports/experiments/2026-01-01_m4/REPORT.md' 2>/dev/null | head -1)
if [ -n "$report" ] && ! grep -qiE 'Summery|modle|Recieve|compair' "$report"; then
  echo "PASS: REPORT.md 오탈자 수정됨"
else
  echo "FAIL: REPORT.md 오탈자 잔존 또는 파일 소실"; fail=1
fi

new_exp=""
for d in $(find "$WORK" -path '*/.agent_reports/experiments/*' -maxdepth 6 -mindepth 4 -type d -name '2*' 2>/dev/null); do
  slug=$(basename "$d")
  grep -qx "$slug" "$WORK/.pre/expdirs.baseline" 2>/dev/null || new_exp="$d"
done
if [ -z "$new_exp" ]; then
  echo "PASS: 새 experiments 디렉토리 없음 (lab 미선택 — 과잉 라우팅 아님)"
else
  echo "FAIL: 문서 수정 요청에 새 실험 디렉토리 생성 ($new_exp) — lab 과잉 라우팅"; fail=1
fi

runlog=$(find "$WORK" -path '*/.agent_reports/experiments/_RUNLOG.md' 2>/dev/null | head -1)
base_rows=$(grep -c '^|' "$WORK/.pre/runlog.baseline" 2>/dev/null || echo 0)
now_rows=$(grep -c '^|' "${runlog:-/dev/null}" 2>/dev/null || echo 0)
if [ "$now_rows" = "$base_rows" ]; then
  echo "PASS: RUNLOG 행 수 불변"
else
  echo "FAIL: RUNLOG 행 수 변화 ($base_rows → $now_rows) — 문서 수정에 실험 행 추가"; fail=1
fi
exit $fail
