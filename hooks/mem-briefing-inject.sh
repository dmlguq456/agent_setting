#!/usr/bin/env bash
# mem-briefing-inject — 아침 논의 데스크 (Cluster F D-26).
#   UserPromptSubmit 마다: cwd==<agent-home>(전용 데스크) AND 오늘 당직 보고 존재 AND 아직 브리핑 안 함
#   → 오늘 당직 보고 + 간밤 처리 요약(전수 보고 D-25)을 additionalContext 로 주입 (하루 1회).
#   기존 '당직 처리해줘' 발화 트리거를 자동화. 세션을 장시간 유지하는 환경이라 SessionStart 가
#   아침에 안 뜸 → 'cron 후 그날 첫 상호작용'(=오늘 보고 존재 + 미브리핑)을 견고한 기준으로.
#
#   Guards (mem-recall-inject 동형):
#     - MEM_DISTILL=1 → exit 0 (distiller 세션 재귀 차단)
#     - hook_event_name ≠ UserPromptSubmit → exit 0
#     - cwd ≠ <agent-home> → exit 0 (전용 데스크 외 세션은 방해 안 함 — 다른 프로젝트 작업 보호)
#     - 오늘 당직 보고 없음(cron 전·루프 고장) → exit 0
#     - 이미 오늘 브리핑함 → exit 0 (하루 1회, .briefing-<date> 상태파일)
#   Read-only: notes·graveyard 읽기만. additionalContext 만 emit (never-block 불변식).
#   Portable CLI:
#     mem-briefing-inject.sh --cwd <dir> [--format text|claude-json]
#
#   등록은 adapter hook 설정이 담당한다.
set -euo pipefail
HOOK_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]:-$0}")" && pwd)"
AGENT_HOME="${AGENT_HOME:-$("$HOOK_DIR/../utilities/agent-home.sh")}"

usage() {
  cat <<'EOF'
usage: mem-briefing-inject.sh --cwd <dir> [--format text|claude-json]

Without arguments, reads Claude hook JSON from stdin and emits Claude hook JSON.
EOF
}

# 재귀가드: distiller 세션이면 trigger X, stdin drain 후 즉시 exit 0.
[ "${MEM_DISTILL:-}" = "1" ] && { cat >/dev/null 2>&1; exit 0; }

EVENT="UserPromptSubmit"
CWD=""
FORMAT="claude-json"

if [ "$#" -gt 0 ]; then
  FORMAT="text"
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --cwd)
        [ "$#" -ge 2 ] || { echo "mem-briefing-inject: --cwd requires a dir" >&2; exit 64; }
        CWD=$2
        shift 2
        ;;
      --format)
        [ "$#" -ge 2 ] || { echo "mem-briefing-inject: --format requires a value" >&2; exit 64; }
        case "$2" in text|claude-json) FORMAT=$2 ;; *) echo "mem-briefing-inject: unknown format: $2" >&2; exit 64 ;; esac
        shift 2
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        echo "mem-briefing-inject: unknown argument: $1" >&2
        usage >&2
        exit 64
        ;;
    esac
  done
  [ -n "$CWD" ] || { echo "mem-briefing-inject: --cwd is required" >&2; exit 64; }
else
  input=$(cat 2>/dev/null || true)
  eval "$(printf '%s' "$input" | python3 -c '
import json, sys, shlex
try: d = json.load(sys.stdin)
except Exception: d = {}
print("EVENT="+shlex.quote(d.get("hook_event_name","") or ""))
print("CWD="+shlex.quote(d.get("cwd","") or ""))
' 2>/dev/null || true)"
  EVENT="${EVENT:-}"; CWD="${CWD:-}"
fi

[ "$EVENT" = "UserPromptSubmit" ] || exit 0
# 전용 데스크 게이트 — agent home 메인 트리 세션만 (worktree 제외, 타 프로젝트 보호)
[ "$CWD" = "$AGENT_HOME" ] || exit 0

TODAY="$(date +%F)"
# MEM_BRIEFING_ONCALL override = 테스트 격리 전용 (production default 불변 — dispatch.sh MEM_PY 동형).
ONCALL="${MEM_BRIEFING_ONCALL:-/home/nas/user/Uihyeop/notes/oncall/$TODAY.md}"
STORE="${MEM_STORE:-$AGENT_HOME/memory}"
STATE="$STORE/.briefing-$TODAY"

[ -f "$ONCALL" ] || exit 0      # 오늘 당직 보고 없음(cron 전·루프 고장) → skip
[ -f "$STATE" ] && exit 0       # 이미 오늘 브리핑함 → skip (하루 1회)

mkdir -p "$STORE" 2>/dev/null || true
: > "$STATE"                    # 하루 1회 마킹 먼저 찍어 중복·동시 방지
# 오래된 briefing 마커 GC (7일+, turn-state GC 패턴 동형)
find "$STORE" -maxdepth 1 -name '.briefing-*' -mtime +7 -delete 2>/dev/null || true

# 간밤 처리 요약 (전수 보고 D-25): graveyard 의 오늘 prune 건수 (되돌림 가능 처리 통보)
GY="$STORE/deleted-records.jsonl"
PRUNED=0
[ -f "$GY" ] && PRUNED="$(grep -c "$TODAY" "$GY" 2>/dev/null || echo 0)"

# 제도화 승격 안건 (D-28): durable 반복 규칙·교훈 — 데스크 cwd(<agent-home>) 기준.
# MEM_PY override = 테스트 격리 (dispatch.sh 동형, production default 불변).
PROMO="$(cd "$AGENT_HOME" 2>/dev/null && python3 "${MEM_PY:-$AGENT_HOME/tools/memory/mem.py}" promote-candidates 2>/dev/null || true)"

# additionalContext 또는 plain text emit — json.dumps escaping (R4: shell interpolation 금지). never-block(|| true).
ONCALL_FILE="$ONCALL" PRUNED="$PRUNED" PROMO="$PROMO" FORMAT="$FORMAT" python3 -c '
import os, json
try:
    body = open(os.environ["ONCALL_FILE"], encoding="utf-8").read()
except Exception:
    body = "(당직 보고 읽기 실패)"
pruned = os.environ.get("PRUNED", "0").strip()
promo = os.environ.get("PROMO", "").strip()
msg = "# \U0001f305 아침 논의 데스크 (오늘 당직 브리핑 — 하루 첫 발화 자동주입)\n\n"
msg += ("사용자 발화에 답하기 *전에* 먼저 이 브리핑을 요약·제시하고 항목별로 논의·처리하라. "
        "되돌릴 수 있고 명백한 것은 직접 처리 후 보고, 판단이 필요한 것만 사용자와 논의한다 "
        "(Cluster F D-25). 사용자가 다른 급한 일을 지시하면 그것을 우선하고 브리핑은 뒤로 "
        "미뤄도 된다 — 안건은 사라지지 않는다.\n\n")
if pruned and pruned != "0":
    msg += f"- 간밤 메모리 정리(prune, graveyard 로 복구가능): {pruned}건\n\n"
msg += "## 오늘 당직 보고\n" + body
if promo:
    msg += ("\n\n## 제도화 승격 안건 (논의 — 어디에 박을지·정말 본질인지)\n"
            "아래는 메모리에 반복 누적된 규칙·교훈이다. 사용자와 논의해 종착지"
            "(runtime bootstrap/CONVENTIONS/DESIGN_PRINCIPLES 문서 · hook · drill 케이스)를 정하고, "
            "반영·drill 검증 후 메모리에서 prune 한다 (D-28).\n" + promo)
if os.environ.get("FORMAT") == "text":
    print(msg)
    raise SystemExit
out = {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": msg}}
print(json.dumps(out, ensure_ascii=False))
' || true

exit 0
