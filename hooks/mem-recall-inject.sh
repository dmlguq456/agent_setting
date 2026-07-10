#!/usr/bin/env bash
# mem-recall-inject — UserPromptSubmit 자동 회상 사전주입.
#   모든 일반 prompt 를 shared mem recall --auto 엔진에 전달하고, 엔진이 선별한
#   고신뢰 결과만 additionalContext 로 메인에 사전주입한다.
#
#   Guards:
#     - MEM_DISTILL=1 → 즉시 exit 0 (distiller 세션 재귀 차단 — 세 hook 다 동일)
#     - hook_event_name ≠ UserPromptSubmit → exit 0 no-op
#     - prompt 없음 → exit 0 no-op
#     - tracked project cwd 아님 / 세션이 untracked → exit 0 no-op
#     - auto recall 결과 없음 → inject 0 exit 0
#
#   Hook 자체는 DB를 직접 쓰지 않는다. access/telemetry 기록은 shared recall engine 계약이 소유한다.
#
#   Cap 환경변수 (context blowup 방지):
#     hit line 최대 3개 (CLI --limit 3 + hook 방어 cap)
#     MEM_RECALL_CHARS  (default/max 1200) — 더 작은 cap만 허용
#
#   Portable CLI:
#     mem-recall-inject.sh --prompt <text> [--cwd <dir>] [--session-id <id>]
#                              [--format text|claude-json]
#
#   등록은 adapter hook 설정이 담당한다 (no-matcher, timeout 10).
#         mem-recall-inject.sh 가 세 번째 MEM_DISTILL=1 재귀가드 honor 훅.
set -euo pipefail
HOOK_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]:-$0}")" && pwd)"
AGENT_HOME="${AGENT_HOME:-$("$HOOK_DIR/../utilities/agent-home.sh")}"

usage() {
  cat <<'EOF'
usage: mem-recall-inject.sh --prompt <text> [--cwd <dir>] [--session-id <id>] [--format text|claude-json]

Without arguments, reads Claude hook JSON from stdin and emits Claude hook JSON.
EOF
}

# 재귀가드 (불변식): distiller 세션이면 trigger X, stdin drain 후 즉시 exit 0.
# drain: 미소비 stdin 으로 인한 pipefail-유발 SIGPIPE/비0 exit 회피
# (정상 경로는 아래 input=$(cat ...) 가 소비하므로 drain 불필요 — guard 발동 시만 필요).
[ "${MEM_DISTILL:-}" = "1" ] && { cat >/dev/null 2>&1; exit 0; }

EVENT="UserPromptSubmit"
SID="default"
PROMPT=""
CWD="$PWD"
FORMAT="claude-json"

if [ "$#" -gt 0 ]; then
  FORMAT="text"
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --prompt)
        [ "$#" -ge 2 ] || { echo "mem-recall-inject: --prompt requires text" >&2; exit 64; }
        PROMPT=$2
        shift 2
        ;;
      --cwd)
        [ "$#" -ge 2 ] || { echo "mem-recall-inject: --cwd requires a dir" >&2; exit 64; }
        CWD=$2
        shift 2
        ;;
      --session-id)
        [ "$#" -ge 2 ] || { echo "mem-recall-inject: --session-id requires an id" >&2; exit 64; }
        SID=$2
        shift 2
        ;;
      --format)
        [ "$#" -ge 2 ] || { echo "mem-recall-inject: --format requires a value" >&2; exit 64; }
        case "$2" in text|claude-json) FORMAT=$2 ;; *) echo "mem-recall-inject: unknown format: $2" >&2; exit 64 ;; esac
        shift 2
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        echo "mem-recall-inject: unknown argument: $1" >&2
        usage >&2
        exit 64
        ;;
    esac
  done
  [ -n "$PROMPT" ] || { echo "mem-recall-inject: --prompt is required" >&2; exit 64; }
else
  input=$(cat 2>/dev/null || true)
  eval "$(printf '%s' "$input" | python3 -c '
import json, sys, shlex
try: d = json.load(sys.stdin)
except Exception: d = {}
print("EVENT="+shlex.quote(d.get("hook_event_name","") or ""))
print("SID="+shlex.quote(d.get("session_id","") or "default"))
print("PROMPT="+shlex.quote(d.get("prompt","") or ""))
print("CWD="+shlex.quote(d.get("cwd","") or ""))
' 2>/dev/null || true)"
  EVENT="${EVENT:-}"; SID="${SID:-default}"; PROMPT="${PROMPT:-}"; CWD="${CWD:-$PWD}"
fi

[ "$EVENT" = "UserPromptSubmit" ] || exit 0
[ -n "${PROMPT//[[:space:]]/}" ] || exit 0

# Project-only/tracked-only gate. Git 프로젝트 또는 상위 artifact root를 프로젝트로 인정하고,
# workflow escape-hatch가 열린 세션에서는 global/project memory를 자동 probe하지 않는다.
PROJECT_ROOT=$(git -C "$CWD" rev-parse --show-toplevel 2>/dev/null || true)
if [ -z "$PROJECT_ROOT" ]; then
  d=$CWD
  while [ -n "$d" ]; do
    if [ -d "$d/.agent_reports" ] || [ -d "$d/.claude_reports" ]; then
      PROJECT_ROOT=$d
      break
    fi
    [ "$d" = "/" ] && break
    parent=$(dirname "$d")
    [ "$parent" = "$d" ] && break
    d=$parent
  done
fi
[ -n "$PROJECT_ROOT" ] || exit 0
for base in \
  "$PROJECT_ROOT/.agent_reports/.untracked" \
  "$PROJECT_ROOT/.claude_reports/.untracked" \
  "$PROJECT_ROOT/.untracked"; do
  [ -f "$base" ] && exit 0
  [ "$SID" != "default" ] && [ -f "$base.$SID" ] && exit 0
done

# shared engine 이 trigger/candidate/coverage/noise 판단을 소유한다. 저신뢰 또는 generic prompt 는
# 빈 stdout 을 반환한다. Hook 은 adapter payload 변환과 최종 context cap 만 담당한다.
RECALL_RUNTIME="${MEM_RECALL_RUNTIME:-unknown}"
[ "$FORMAT" = "claude-json" ] && RECALL_RUNTIME="${MEM_RECALL_RUNTIME:-claude}"
recall_out=$(cd "$CWD" 2>/dev/null \
  && MEM_RECALL_RUNTIME="$RECALL_RUNTIME" \
     python3 "$AGENT_HOME/tools/memory/mem.py" recall "$PROMPT" --auto --limit 3 2>/dev/null \
  || true)

# CLI limit 이 깨져도 hook 이 최대 3 hit line 만 싣도록 방어한다. optional heading 은 한 줄만
# 보존하고, 기존 "  [tier/scope/type] id: snippet" 형식 외 출력은 버린다.
capped=$(printf '%s' "$recall_out" | awk '
  /^#/ { if (!heading) { print; heading=1 }; next }
  /^  \[/ { if (hits < 3) { print; hits++ } }
' 2>/dev/null || true)

# Empty-result/malformed-result no-op. 자동 주입은 hit-line 외 출력을 컨텍스트로 올리지 않는다.
if ! printf '%s' "$capped" | grep -qP '^ {2}\[' 2>/dev/null; then
  # grep -P 미지원 환경 fallback
  if ! printf '%s' "$capped" | grep -q '^  \[' 2>/dev/null; then
    exit 0
  fi
fi

# additionalContext JSON 또는 plain text 출력 — json.dumps 로 escaping (R4: shell interpolation 절대 금지).
# Korean / 따옴표 / 개행 / 스니펫 마커가 recall 출력에 포함될 수 있음.
# 글자 수 cap 은 여기서 문자 슬라이스(b[:N])로 — 멀티바이트 경계 안전.
# '|| true': emit 이 어떤 이유로든 실패해도 hook 은 항상 exit 0 (never-block 불변식).
if [ "$FORMAT" = "text" ]; then
  REC_BLOCK="$capped" MAX_CHARS="${MEM_RECALL_CHARS:-1200}" python3 -c '
import os
try:
    requested = int(os.environ.get("MAX_CHARS", "1200"))
except ValueError:
    requested = 1200
cap = min(max(requested, 0), 1200)
label = "# 🧠 과거 기억 회상 (recall 자동주입 — 고신뢰 매칭)\n"
print((label + os.environ["REC_BLOCK"])[:cap])
' || true
  exit 0
fi

REC_BLOCK="$capped" MAX_CHARS="${MEM_RECALL_CHARS:-1200}" python3 -c '
import os, json
try:
    requested = int(os.environ.get("MAX_CHARS", "1200"))
except ValueError:
    requested = 1200
cap = min(max(requested, 0), 1200)
label = "# \U0001f9e0 과거 기억 회상 (recall 자동주입 — 고신뢰 매칭)\n"
payload = (label + os.environ["REC_BLOCK"])[:cap]
out = {
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": payload
    }
}
print(json.dumps(out, ensure_ascii=False))
' || true

exit 0
