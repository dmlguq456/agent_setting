#!/bin/bash
# g8b_design_verifier_clean_pass assert — FILE-BASED (g8 의 대칭 제어)
#
# 설계 원칙:
#   - clean fixture(에러·깨짐 없음)에 verifier 가 breakage / needs_work 를 반환하면 FAIL.
#   - 금지된 결과 = "멀쩡한 파일인데 과잉 실패" (g8 의 반대 방향).
#   - clean fixture 에 verdict:done + 깨짐 없음 = 정상 통과 → PASS.
#
# Sub-check A (hard FAIL — 대칭 금지 결과):
#   - verifier 파일에 breakage:has_errors 또는 verdict:needs_work 가 있고,
#     AND 실제 console/overflow/overlap 에러가 fixture 에 없음이 확인될 때 FAIL.
#   (주의: 판단 여지가 있는 [vis] 항목 실패는 과잉 실패가 아님 → needs_iteration / needs_review 는 soft only)
#
# Sub-check B (soft WARN):
#   - verdict:done 또는 status:verified 흔적 → PASS-soft
#   - breakage:has_errors 또는 verdict:needs_work 흔적 → WARN (과잉 실패 가능성)
set -u
WORK=$1
T=$2  # final-result transcript — 사용 안 함 (file-based)
fail=0

VERIFIER_FILE=""
if [ -f "$WORK/repo/verifier_out.md" ]; then
  VERIFIER_FILE="$WORK/repo/verifier_out.md"
else
  found=$(find "$WORK/repo/.claude_reports" -path "*/04_review/verifier.md" 2>/dev/null | head -1)
  [ -n "$found" ] && VERIFIER_FILE="$found"
fi

if [ -n "$VERIFIER_FILE" ]; then
  echo "INFO: verifier 파일 발견 → $VERIFIER_FILE"

  # --- Sub-check A: hard FAIL — clean fixture 에 breakage hard-fail 반환? ---
  has_errors=0
  has_needs_work=0
  has_done=0

  grep -qiE "breakage.*has_errors|has_errors.*breakage" "$VERIFIER_FILE" 2>/dev/null && has_errors=1
  grep -qiE "verdict\s*:\s*needs_work"                  "$VERIFIER_FILE" 2>/dev/null && has_needs_work=1
  grep -qiE "verdict\s*:\s*done|status\s*:\s*verified"  "$VERIFIER_FILE" 2>/dev/null && has_done=1

  # 금지된 결과: clean fixture 에 breakage:has_errors 또는 verdict:needs_work
  # (needs_iteration / needs_review 는 [vis] 판단이므로 soft only — hard FAIL 대상 아님)
  if [ "$has_errors" = "1" ] || [ "$has_needs_work" = "1" ]; then
    echo "FAIL [Sub-check A]: verifier 가 clean fixture 에 과잉 실패 반환"
    echo "  → breakage:has_errors($has_errors) 또는 verdict:needs_work($has_needs_work) 있음"
    echo "  → 깨끗한 HTML 에 Layer-1 hard-fail 은 over-strict verifier 를 나타냄"
    fail=1
  else
    echo "PASS [Sub-check A]: clean fixture 에 breakage 과잉 실패 없음"
  fi

  # --- Sub-check B: soft — 정상 통과 흔적 ---
  if [ "$has_done" = "1" ]; then
    echo "PASS-soft [Sub-check B]: verdict:done 또는 status:verified 확인 — clean fixture 정상 통과"
  else
    echo "WARN [Sub-check B]: verdict:done / status:verified 흔적 없음 — wording 변형 또는 미완 출력 (turn-cap 가능)"
  fi

else
  echo "WARN: verifier 파일 없음 ($WORK/repo/verifier_out.md 및 04_review/verifier.md 모두 부재)"
  echo "  → MCP 없는 헤드리스에서 렌더 불가이거나 verifier 가 파일을 기록하지 않음"
  echo "  → MCP-free backstop: clean fixture 는 콘솔 에러 없으므로 console-check.mjs exit 0 기대"

  CONSOLE_CHECK="$HOME/.claude/tools/design-mcp/console-check.mjs"
  PREVIEW="$WORK/repo/preview.html"

  if [ -f "$CONSOLE_CHECK" ] && [ -f "$PREVIEW" ]; then
    if node "$CONSOLE_CHECK" "$PREVIEW" 2>/tmp/g8b_console_check_err.txt; then
      echo "PASS-soft [MCP-free backstop]: console-check.mjs exit 0 — clean HTML 콘솔 에러 없음 확인"
    else
      cc_exit=$?
      echo "WARN [MCP-free backstop]: console-check.mjs exit $cc_exit — 예상 외 콘솔 에러 (fixture 문제?)"
      cat /tmp/g8b_console_check_err.txt 2>/dev/null || true
    fi
  else
    echo "WARN [MCP-free backstop]: console-check.mjs 또는 preview.html 없음 — 직접 확인 불가"
  fi
  # verifier 파일 없으면 hard-FAIL 불가 (확인 불가 → 케이스 unpromotable)
fi

exit $fail
