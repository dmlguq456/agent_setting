#!/usr/bin/env bash
# mem-recall-inject — D-15 B1 완성: 회상 신호어 자동 사전주입 (DESIGN_PRINCIPLES §0.5, spec v9 Cluster D).
#   UserPromptSubmit 마다 한국어 신호어(지난번|예전에|전에 등)를 regex 감지, 매칭 시
#   mem recall 을 실행해 결과를 additionalContext 로 메인에 사전주입. 메인의 "recall 할까"
#   판단을 결정론 hook 이 대체 (B1 완성 — CLAUDE.md §2 회상 신호어 자율 트리거).
#
#   Guards:
#     - MEM_DISTILL=1 → 즉시 exit 0 (distiller 세션 재귀 차단 — 세 hook 다 동일)
#     - hook_event_name ≠ UserPromptSubmit → exit 0 no-op
#     - 신호어 미감지 → exit 0 no-op (압도적 다수 정상 경로)
#     - recall 결과에 실제 hit-line 없음(header-only / 매칭 없음) → inject 0 exit 0 (empty-result no-op)
#
#   Read-only 불변식: mem recall 은 DB write 0. additionalContext 만 emit — 메인 상태 무변경.
#
#   Cap 환경변수 (context blowup 방지):
#     MEM_RECALL_LINES  (default 12) — 주입할 최대 줄 수
#     MEM_RECALL_CHARS  (default 2000) — 주입할 최대 글자 수 (python 문자 슬라이스 — UTF-8 경계 안전)
#
#   등록: settings.json hooks.UserPromptSubmit 4번째 항목 (no-matcher, timeout 10).
#         mem-recall-inject.sh 가 세 번째 MEM_DISTILL=1 재귀가드 honor 훅.
set -euo pipefail
AGENT_HOME="${AGENT_HOME:-${CLAUDE_HOME:-$HOME/.claude}}"

# 재귀가드 (불변식): distiller 세션이면 trigger X, stdin drain 후 즉시 exit 0.
# drain: 미소비 stdin 으로 인한 pipefail-유발 SIGPIPE/비0 exit 회피
# (정상 경로는 아래 input=$(cat ...) 가 소비하므로 drain 불필요 — guard 발동 시만 필요).
[ "${MEM_DISTILL:-}" = "1" ] && { cat >/dev/null 2>&1; exit 0; }

input=$(cat 2>/dev/null || true)
eval "$(printf '%s' "$input" | python3 -c '
import json, sys, shlex
try: d = json.load(sys.stdin)
except Exception: d = {}
print("EVENT="+shlex.quote(d.get("hook_event_name","") or ""))
print("SID="+shlex.quote(d.get("session_id","") or "default"))
print("PROMPT="+shlex.quote(d.get("prompt","") or ""))
' 2>/dev/null || true)"
EVENT="${EVENT:-}"; SID="${SID:-default}"; PROMPT="${PROMPT:-}"

[ "$EVENT" = "UserPromptSubmit" ] || exit 0

# 신호어 regex (D-15 canonical PAT — MEMORY §7.5 + 테스트 픽스처와 동일 출처):
# 순수 리터럴 alternation (no \b / char-ranges — 로케일 해저드 회피).
# 주의: bare top-level [[ =~ ]] 는 set -e 하에서 no-match 시 스크립트를 exit 1 로 종료함.
# 아래 '|| exit 0' 가드 형식으로 no-match 를 clean no-op 으로 처리한다.
PAT='지난번|지난번에|예전에|이전에|전에|그때|저번에|아까'
[[ "${PROMPT:-}" =~ $PAT ]] || exit 0

# 신호어 감지 — mem recall 실행 (deployed path, mem.py L426-529 recall(), read-only)
recall_out=$(python3 "$AGENT_HOME/tools/memory/mem.py" recall "$PROMPT" 2>/dev/null || true)

# 결과 cap (context blowup 방지) — env-overridable
# 줄 수만 shell(head -n)로 cap. 글자 수 cap 은 아래 python emit 에서 문자 슬라이스로 —
# head -c 는 바이트 절단이라 한글(3바이트) 중간을 끊어 깨진 시퀀스를 만들 수 있음.
MAX_LINES="${MEM_RECALL_LINES:-12}"

capped=$(printf '%s' "$recall_out" | head -n "$MAX_LINES" 2>/dev/null || true)

# Empty-result no-op: recall 은 항상 "# recall:" 헤더를 출력.
# 실제 hit-line 은 "  [{tier}/{scope}/{type}] {id}: {snip}" 형식 (두 칸 들여쓰기 + '[' 시작).
# hit-line 없으면 inject 0 — (store 매칭 없음) / (store 없음) 등 header-only 케이스.
if ! printf '%s' "$capped" | grep -qP '^ {2}\[' 2>/dev/null; then
  # grep -P 미지원 환경 fallback
  if ! printf '%s' "$capped" | grep -q '^  \[' 2>/dev/null; then
    exit 0
  fi
fi

# additionalContext JSON 출력 — json.dumps 로 escaping (R4: shell interpolation 절대 금지).
# Korean / 따옴표 / 개행 / 스니펫 마커가 recall 출력에 포함될 수 있음.
# 글자 수 cap 은 여기서 문자 슬라이스(b[:N])로 — 멀티바이트 경계 안전.
# '|| true': emit 이 어떤 이유로든 실패해도 hook 은 항상 exit 0 (never-block 불변식).
REC_BLOCK="$capped" MAX_CHARS="${MEM_RECALL_CHARS:-2000}" python3 -c '
import os, json
b = os.environ["REC_BLOCK"][: int(os.environ.get("MAX_CHARS", "2000"))]
label = "# \U0001f9e0 과거 기억 회상 (recall 자동주입 — 신호어 감지)\n"
out = {
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": label + b
    }
}
print(json.dumps(out, ensure_ascii=False))
' || true

exit 0
