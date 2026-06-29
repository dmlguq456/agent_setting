#!/bin/bash
# loops 공용 헬퍼 — source 전용 (직접 실행하지 않는다).
# study.sh·oncall.sh 가 LOG 변수 정의 직후 `source "$LOOP_DIR/lib.sh"` 한다.

# --- 버그①: cron 환경 PATH 보정 ---
# cron 의 제한 PATH 는 /usr/bin/node(v10) 를 집어, claude 가 SessionEnd 때 codex 플러그인
# hook(.mjs, `import ... "node:fs"`)을 실행하다 ESM/`node:` 스킴을 못 읽어 SyntaxError 로
# 죽었다 (2026-06-21 연수 사고). ~/.local/bin(v20) 을 앞세워 cron 에서도 최신 node 가 잡히게.
export PATH="$HOME/.local/bin:$PATH"

# --- 버그②: claude -p 일시장애 재시도 래퍼 ---
# 사용:  run_claude_retry <timeout초> <프롬프트파일> [claude 추가인자...]
#   401·5xx·overloaded·rate-limit = *일시* 장애 → 백오프 후 재시도 (최대 3회).
#   session/usage limit = 리셋 전엔 안 풀림 → 즉시 ABORT (재시도 무의미).
#   매 시도 출력은 stdout 으로 그대로 흘리고, 종료 사유를 마커로 남긴다 (당직이 점검).
run_claude_retry() {
  local to="$1" pf="$2"; shift 2
  local max=3 attempt rc out
  local backoff=(0 30 120)   # 시도 전 대기 (1회차 0s)
  for ((attempt = 1; attempt <= max; attempt++)); do
    if [ "${backoff[attempt-1]}" -gt 0 ]; then
      echo "=== retry $attempt/$max — ${backoff[attempt-1]}s 대기 후 재시도 ==="
      sleep "${backoff[attempt-1]}"
    fi
    out="$(timeout "$to" "$HOME/.local/bin/claude" -p "$(cat "$pf")" "$@" 2>&1)"
    rc=$?
    printf '%s\n' "$out"
    # 사용량 제한 — 리셋 전엔 안 풀리므로 재시도하지 않고 명확히 끝낸다
    if printf '%s' "$out" | grep -qiE 'session limit|usage limit|hit your .*limit'; then
      echo "=== ABORT: session/usage limit — 재시도 무의미 (rc=$rc, attempt=$attempt) ==="
      return 2
    fi
    # 성공 = 종료 0 + 일시오류 마커 없음
    if [ "$rc" -eq 0 ] && ! printf '%s' "$out" \
        | grep -qiE '401|invalid authentication|overloaded|rate.?limit|internal server error|api error: 5[0-9][0-9]'; then
      return 0
    fi
  done
  echo "=== FAILED after $max attempts (rc=$rc) ==="
  return 1
}
