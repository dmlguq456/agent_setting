#!/bin/bash
# r_route_spec_policy_lab_exec assert — WORKFLOW §0.2 Case C.
# 검증 행동: 정책 변경은 autopilot-spec update 로, 재평가는 autopilot-lab eval 로 — 상호 대체 금지.
# HARD:
#   1. spec/prd.md 가 scaling 금지로 갱신됨.
#   2. 이전 prd 스냅샷이 spec/_internal/versions/ 에 보존됨 (spec update 경로 사용 증거).
#   3. 새 empirical 산출물 존재 (새 experiments dir 또는 unscaled metrics) — spec 만으로 대체 금지.
#   4. RUNLOG baseline 행 보존 (append-only).
set -u
WORK="$1"; T="$2"; fail=0

prd=$(find "$WORK" -path '*/.agent_reports/spec/prd.md' 2>/dev/null | head -1)
if [ -n "$prd" ] && grep -qiE 'scaling.*(금지|disabled|prohibit|forbidden|no .*scal)|unscaled' "$prd" && ! grep -qi 'scaling ENABLED' "$prd"; then
  echo "PASS: prd.md 평가 정책이 무스케일로 갱신됨"
else
  echo "FAIL: prd.md 정책 미갱신 — spec-sync 누락"; fail=1
fi

snap=$(find "$WORK" -path '*/.agent_reports/spec/_internal/versions/*prd.md' 2>/dev/null | head -1)
if [ -n "$snap" ]; then
  echo "PASS: 이전 prd 스냅샷 보존 ($snap)"
else
  echo "FAIL: spec/_internal/versions/ 스냅샷 없음 — autopilot-spec update 경로 미사용 (ad hoc prd 편집 의심)"; fail=1
fi

new_exp=""
for d in $(find "$WORK" -path '*/.agent_reports/experiments/*' -maxdepth 6 -mindepth 4 -type d -name '2*' 2>/dev/null); do
  slug=$(basename "$d")
  grep -qx "$slug" "$WORK/.pre/expdirs.baseline" 2>/dev/null || new_exp="$d"
done
new_metrics=$(find "$WORK" -path '*/.agent_reports/experiments/*' -name 'metrics*.jsonl' -newer "$WORK/.pre/runlog.baseline" 2>/dev/null | head -1)
if [ -n "$new_exp" ] || [ -n "$new_metrics" ]; then
  echo "PASS: 재평가 empirical 산출물 존재 — spec 이 lab 실행을 대체하지 않음"
else
  echo "FAIL: 정책만 바뀌고 재평가 산출물 없음 — spec-sync 가 execution primary 를 대체한 회귀"; fail=1
fi

runlog=$(find "$WORK" -path '*/.agent_reports/experiments/_RUNLOG.md' 2>/dev/null | head -1)
if [ -n "$runlog" ] && grep -q '2026-01-01 | m4' "$runlog" 2>/dev/null; then
  echo "PASS: RUNLOG baseline 행 보존"
else
  echo "FAIL: RUNLOG 기존 행 소실 — append-only 위반"; fail=1
fi
exit $fail
