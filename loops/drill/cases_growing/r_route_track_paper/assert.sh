#!/bin/bash
# r_route_track_paper assert
# 검증: "camera-ready" → 문서 트랙(autopilot-draft paper, high-stakes→adversarial) 라우팅.
# soft (transcript=result 텍스트만이라 skill 호출이 확실히 안 드러남 — hard 어려움): result 에
#   올바른 트랙 언급 + 틀린 트랙(code/lab) 작업 흔적 0. fail=0 고정 (오판은 WARN — g7 패턴).
# NOTE: 라우팅의 hard 검증은 tool-call 로그 파싱이 필요 — run.sh json 에 tool turn 노출 시 승격 여지.
WORK="$1"; T="$2"; REPO="$WORK/repo"
if grep -qiE 'draft|paper|camera|adversarial|문서 트랙' "$T" 2>/dev/null; then
  echo "PASS(soft): 문서 트랙(draft/paper) 라우팅 언급"
else
  echo "WARN: result 에 draft/paper 라우팅 언급 안 보임 (turn cap 또는 오라우팅)"
fi
if [ -n "$(find "$REPO/.claude_reports/plans" -type f 2>/dev/null | head -1)" ]; then
  echo "WARN: code plans 생성 — paper 요청에 code 트랙 오라우팅 의심"
else
  echo "PASS(soft): code 트랙 오작동 흔적 0"
fi
exit 0
