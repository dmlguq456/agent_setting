#!/usr/bin/env sh
# usage-check — SD-16(a) 사용량-인지 상호보완 크로스 하네스 분사의 사용량 조회 헬퍼
#   (OPERATIONS §5.10 ⑧). orchestrator(main/conductor)가 분사 _전_ Claude·Codex 양 하네스의
#   limit 상태를 결정론적으로 조회해 harness 별 `{ok | limited(<reset>) | unknown}` 를 낸다.
#
#   ⚠️ 조회 표면 한계 (runtime-currentness, 2026-07 조사): Claude `/usage`·Codex `/status` 는
#   대화형 슬래시 커맨드뿐 — 스크립트 가능한 headless 사용량 API 가 없다(Codex 는 openai/codex
#   #15281 이 open feature). 따라서 본 헬퍼는 공식 표면 대신 **보수 조회**:
#     · jobs.log 의 `note=dead-*limit*` 마커(SD-15 wrapper 가 심음, OPERATIONS §5.10 ⑨)
#     · `.dispatch/usage-reset.<harness>` reset 캐시(SD-15 가 씀)
#   판정:
#     · limited(<reset>) — window(기본 300분=5h rolling) 안에 dead-limit 마커가 있음.
#     · ok              — 활성 limit 마커 없음. **가용 보장이 아니라 "알려진 차단 없음"** 이다.
#     · unknown         — jobs.log 부재/해석 불가 → 조회 실패로 취급(막지 말고 orchestrator 판단).
#
#   사용: usage-check.sh [--harness claude|codex|all] [--jobs <path>] [--window-min <N>]
#   출력: harness 당 한 줄 `<harness> <state>` (파싱 가능). exit 0 항상(informational).
set -u

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
AGENT_HOME="${AGENT_HOME:-$("$SCRIPT_DIR/agent-home.sh")}"

HARNESS="all"
JOBS=""
WINDOW_MIN=300
while [ $# -gt 0 ]; do
  case "$1" in
    --harness) HARNESS="${2:-all}"; shift 2 ;;
    --jobs) JOBS="${2:-}"; shift 2 ;;
    --window-min) WINDOW_MIN="${2:-300}"; shift 2 ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "usage-check: unknown arg '$1'" >&2; exit 64 ;;
  esac
done
[ -n "$JOBS" ] || JOBS="$AGENT_HOME/.dispatch/jobs.log"
case "$HARNESS" in all) HARNESSES="claude codex" ;; *) HARNESSES="$HARNESS" ;; esac

now=$(date +%s)

# epoch(ts) — ISO8601(…Z) → epoch, 실패 시 0.
to_epoch() { date -d "$(printf '%s' "$1" | sed 's/Z$/ UTC/')" +%s 2>/dev/null || echo 0; }

# harness 의 가장 최근 dead-limit 마커를 찾는다. 출력: "<epoch> <reset>" 또는 빈 문자열.
latest_limit_marker() { # $1=harness
  h=$1
  [ -f "$JOBS" ] || return 0
  awk -F'\t' -v h="$h" '
    $6 ~ /note=dead-[a-z-]*limit/ {
      # harness= 또는 owner_harness= 가 h 와 일치하는 row 만.
      if ($6 ~ ("harness=" h) || $6 ~ ("owner_harness=" h)) {
        reset="-"
        n=split($6, kv, ",")
        for (i=1;i<=n;i++) { if (kv[i] ~ /^reset=/) { reset=substr(kv[i],7) } }
        print $1 "\t" reset
      }
    }' "$JOBS" | sort | tail -1
}

for h in $HARNESSES; do
  state="ok"
  marker=$(latest_limit_marker "$h")
  reset="-"
  if [ -n "$marker" ]; then
    mts=$(printf '%s' "$marker" | cut -f1)
    reset=$(printf '%s' "$marker" | cut -f2)
    mepoch=$(to_epoch "$mts")
    age_min=$(( (now - mepoch) / 60 ))
    if [ "$mepoch" -gt 0 ] && [ "$age_min" -lt "$WINDOW_MIN" ]; then
      state="limited(${reset:--})"
    fi
  fi
  # jobs.log 자체가 없으면 조회 불가 = unknown.
  [ -f "$JOBS" ] || state="unknown"
  printf '%s %s\n' "$h" "$state"
done
