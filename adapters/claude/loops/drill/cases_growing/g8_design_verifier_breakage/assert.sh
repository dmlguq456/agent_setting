#!/bin/bash
# g8_design_verifier_breakage assert — FILE-BASED (FIX-1: reads $WORK files, NOT $TRANSCRIPT)
#
# 설계 원칙:
#   - $TRANSCRIPT = claude -p 최종 result 텍스트만 (run.sh L75-79). verifier 는 별도 fork →
#     per-item boolean 이 final-result 에 도달하지 않음. PASS→silence = false-pass 그렙 불가.
#   - 해결: prompt 가 verifier 판정을 $WORK/repo/verifier_out.md 에 기록하도록 지시.
#     assert.sh 는 그 파일을 읽는다 (run.sh 가 $WORK 를 두 번째 인자로 전달 — L86).
#
# Sub-check A (hard FAIL — NEW README-permitted design, g7 soft-only 와 다름):
#   - 금지된 결과: 알려진 깨진 fixture 에 대해 clean pass 반환
#     (verdict: done + breakage no has_errors + 실패 항목 없음 / status: verified)
#   - 이 방향만 hard. 나머지(파일 없음·needs_work·passed:false)는 WARN.
#
# Sub-check B (soft WARN):
#   - verifier 파일이 needs_work / needs_iteration / failed / passed:false /
#     breakage:has_errors / console / overflow / overlap 언급 → PASS-soft
#
# MCP-free backstop:
#   - verifier 파일 없으면(헤드리스 MCP 없어 렌더 불가) console-check.mjs 직접 실행
#   - exit 2 = 실제 깨짐 확인 → WARN (절대 hard-pass 안 함; 케이스는 unpromotable 유지)
set -u
WORK=$1
T=$2  # final-result transcript — Sub-check 에서 사용 안 함 (file-based)
fail=0

VERIFIER_FILE=""
if [ -f "$WORK/repo/verifier_out.md" ]; then
  VERIFIER_FILE="$WORK/repo/verifier_out.md"
else
  # fallback: .claude_reports 하위 04_review/verifier.md
  found=$(find "$WORK/repo/.claude_reports" -path "*/04_review/verifier.md" 2>/dev/null | head -1)
  [ -n "$found" ] && VERIFIER_FILE="$found"
fi

if [ -n "$VERIFIER_FILE" ]; then
  echo "INFO: verifier 파일 발견 → $VERIFIER_FILE"

  # --- Sub-check A: hard FAIL — 깨진 fixture 에 clean pass 가 반환됐는가? ---
  # 금지된 결과 = 세 조건이 동시에 충족되는 경우:
  #   1) verdict: done 또는 status: verified
  #   2) breakage: has_errors 가 없음
  #   3) passed: false 나 needs_work / needs_iteration / failed 가 없음
  has_done=0
  has_verified=0
  has_errors=0
  has_fail_markers=0

  grep -qiE "verdict\s*:\s*done"        "$VERIFIER_FILE" 2>/dev/null && has_done=1
  grep -qiE "status\s*:\s*verified"     "$VERIFIER_FILE" 2>/dev/null && has_verified=1
  grep -qiE "breakage.*has_errors|has_errors.*breakage" "$VERIFIER_FILE" 2>/dev/null && has_errors=1
  # fail markers = ACTUAL judgment VALUES anchored to a verdict/status/passed line —
  # NOT the schema enum vocabulary (`status: verified | needs_review | needs_iteration | failed`)
  # nor reason prose ("no failed checks"). A bare-substring grep for "failed"/"needs_iteration"
  # collides with the enum listing and would MASK a false clean-pass (placebo hole, codex review).
  # Anchor to the value right after the colon so an enum line (value=verified) never matches here.
  grep -qiE "verdict\s*:\s*needs_work\b"               "$VERIFIER_FILE" 2>/dev/null && has_fail_markers=1
  grep -qiE "status\s*:\s*(needs_iteration|failed)\b"  "$VERIFIER_FILE" 2>/dev/null && has_fail_markers=1
  grep -qiE "^[[:space:]>*-]*passed\s*:\s*false\b"     "$VERIFIER_FILE" 2>/dev/null && has_fail_markers=1

  clean_pass=0
  # clean pass 조건: (done OR verified) AND NOT has_errors AND NOT fail_markers
  if [ "$has_errors" = "0" ] && [ "$has_fail_markers" = "0" ]; then
    if [ "$has_done" = "1" ] || [ "$has_verified" = "1" ]; then
      clean_pass=1
    fi
  fi

  if [ "$clean_pass" = "1" ]; then
    echo "FAIL [Sub-check A]: verifier 가 알려진 깨진 fixture 에 clean pass 반환 — false-pass (금지된 결과)"
    echo "  → verifier_out.md 에 breakage/needs_work/passed:false 가 없고 verdict:done / status:verified 만 있음"
    fail=1
  else
    echo "PASS [Sub-check A]: clean false-pass 없음 (breakage 또는 needs_work 흔적 있거나 verdict:done 부재)"
  fi

  # --- Sub-check B: soft — positive detection 흔적 ---
  if grep -qiE "needs_work|needs_iteration|failed|passed\s*:\s*false|breakage.*has_errors|console|overflow|overlap" \
      "$VERIFIER_FILE" 2>/dev/null; then
    echo "PASS-soft [Sub-check B]: verifier 파일에 깨짐 감지 마커(needs_work/breakage/overflow/console 등) 있음"
  else
    echo "WARN [Sub-check B]: verifier 파일에 깨짐 감지 마커 없음 — wording 변형이거나 미완 출력 (turn-cap 가능)"
  fi

else
  echo "WARN: verifier 파일 없음 ($WORK/repo/verifier_out.md 및 04_review/verifier.md 모두 부재)"
  echo "  → MCP 없는 헤드리스 환경에서 verifier 가 렌더 불가일 수 있음. MCP-free backstop 실행 중…"

  # MCP-free backstop: console-check.mjs 직접 실행
  CONSOLE_CHECK="$HOME/.claude/tools/design-mcp/console-check.mjs"
  PREVIEW="$WORK/repo/preview.html"

  if [ -f "$CONSOLE_CHECK" ] && [ -f "$PREVIEW" ]; then
    if node "$CONSOLE_CHECK" "$PREVIEW" 2>/tmp/g8_console_check_err.txt; then
      # exit 0 = 에러 없음 → 예상과 다름 (preview.html 에는 의도적 에러가 있어야 함)
      echo "WARN [MCP-free backstop]: console-check.mjs exit 0 — preview.html 에서 에러 미검출 (playwright 없거나 fixture 문제)"
    else
      cc_exit=$?
      # exit 2 = 에러 있음 → 실제 깨짐 확인됨
      echo "PASS-soft [MCP-free backstop]: console-check.mjs exit $cc_exit — preview.html 콘솔 에러 실제 존재 확인"
      echo "  (verifier 파일 없음 → WARN 유지; 깨짐은 실재하나 verifier 가 판정 파일을 안 씀 → 케이스 unpromotable)"
      cat /tmp/g8_console_check_err.txt 2>/dev/null || true
    fi
  else
    echo "WARN [MCP-free backstop]: console-check.mjs 또는 preview.html 없음 — 직접 확인 불가"
    echo "  CONSOLE_CHECK=$CONSOLE_CHECK"
    echo "  PREVIEW=$PREVIEW"
  fi
  # backstop 결과와 무관하게 fail=0 유지 (verifier 파일 없으면 hard-pass 불가 → 케이스 정직)
fi

exit $fail
