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
#   판정 (SD-16e §8.6.2 reset 의미론):
#     · limited(<reset>)      — window(기본 300분=5h rolling) 안 dead-limit 마커 + reset= 미경과.
#     · limited(unknown-reset)— dead-limit 마커에 reset= 이 없음. 해제 시각 미상 → orchestrator 가
#                               "확인 필요"로 읽어야 함. UNKNOWN_WINDOW_MIN(기본 60분) 안에서만 이 상태,
#                               넘기면 ok 로 downgrade(근거 없는 5h 봉쇄 방지).
#     · ok                    — 활성 limit 마커 없음 / reset= 경과(expired) / unknown-reset 창 초과.
#                               **가용 보장이 아니라 "알려진 차단 없음"**. → 수동 마감 시 reset= 기입 의무
#                               (OPERATIONS §5.10 jobs.log 하드 계약).
#     · unknown               — jobs.log 부재/해석 불가 → 조회 실패로 취급(막지 말고 orchestrator 판단).
#
#   사용: usage-check.sh [--harness claude|codex|all] [--jobs <path>] [--window-min <N>]
#   출력: harness 당 한 줄 `<harness> <state>` (파싱 가능) + 마지막 한 줄 `bias <harness>`.
#   exit 0 항상(informational).
#
#   한도 비대칭 기본값 (SD-OPEN-3, 사용자 제공 2026-07-10): 현행 가정 = Claude Code 한도 > Codex
#   → 분산 기본 방향(bias) = claude 주력, codex 는 교차 리뷰·failover 고가치 자리 우선.
#   **가변 전제 — 하드코드 금지**: `HARNESS_CAPACITY_BIAS` env 로 교체(예: codex), 미설정 시 claude.
set -u

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
AGENT_HOME="${AGENT_HOME:-$("$SCRIPT_DIR/agent-home.sh")}"

HARNESS="all"
JOBS=""
WINDOW_MIN=300
# SD-16e (§8.6.2): reset= 없는 마커는 해제 시각을 모르므로 보수 창을 단축한다 — 이 창 안에서만
# `limited(unknown-reset)` 로 표기하고, 창을 넘기면 `ok` 로 downgrade 해 reset-less 마커가 전체
# WINDOW_MIN(5h) 내내 하네스를 봉쇄하지 않게 한다. env 로 교체 가능(하드코드 금지).
UNKNOWN_WINDOW_MIN="${UNKNOWN_WINDOW_MIN:-60}"
while [ $# -gt 0 ]; do
  case "$1" in
    --harness) HARNESS="${2:-all}"; shift 2 ;;
    --jobs) JOBS="${2:-}"; shift 2 ;;
    --window-min) WINDOW_MIN="${2:-300}"; shift 2 ;;
    --unknown-window-min) UNKNOWN_WINDOW_MIN="${2:-60}"; shift 2 ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "usage-check: unknown arg '$1'" >&2; exit 64 ;;
  esac
done
[ -n "$JOBS" ] || JOBS="$AGENT_HOME/.dispatch/jobs.log"
case "$HARNESS" in all) HARNESSES="claude codex" ;; *) HARNESSES="$HARNESS" ;; esac

now=$(date +%s)

# epoch(ts) — ISO8601(…Z) → epoch, 실패 시 0.
to_epoch() { date -d "$(printf '%s' "$1" | sed 's/Z$/ UTC/')" +%s 2>/dev/null || echo 0; }

# SD-16e (§8.6.2): reset= clock 문자열(3pm·noon·15:45·1pm…)을 epoch 로. reset 은 마커 시각
# 이후 첫 도래로 해석한다 — 파싱한 clock 이 마커 epoch 보다 이르면 다음날로 넘긴다. 파싱 불가·부재면 0.
reset_to_epoch() { # $1=reset 문자열, $2=marker epoch ; echo epoch(>0) 또는 0
  r=$1; mep=$2
  case "$r" in ''|-|unknown|unknown-reset) echo 0; return ;; esac
  # noon/midnight 를 date 가 이해하는 clock 으로 정규화.
  r=$(printf '%s' "$r" | sed 's/[Nn][Oo][Oo][Nn]/12pm/; s/[Mm][Ii][Dd][Nn][Ii][Gg][Hh][Tt]/12am/')
  e=$(date -d "$r" +%s 2>/dev/null || echo 0)
  [ "${e:-0}" -gt 0 ] 2>/dev/null || { echo 0; return; }
  # date -d "3pm" 는 오늘 기준 — 마커가 그 시각 이후였다면 리셋은 다음날 같은 시각.
  if [ "$mep" -gt 0 ] && [ "$e" -lt "$mep" ]; then e=$((e + 86400)); fi
  echo "$e"
}

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
      # SD-16e (§8.6.2): reset 의미론. 마커 시각이 WINDOW_MIN 안이어도 reset 을 반영한다.
      reset_epoch=$(reset_to_epoch "$reset" "$mepoch")
      if [ "$reset_epoch" -gt 0 ]; then
        # reset= 있고 파싱됨 — 경과했으면 ok(expired), 아니면 limited(reset).
        if [ "$now" -ge "$reset_epoch" ]; then
          state="ok"
        else
          state="limited(${reset})"
        fi
      else
        # reset= 부재/파싱불가 — 해제 시각 미상. 보수 창 단축 + 구분 표기(둘 다):
        # UNKNOWN_WINDOW_MIN 안에서만 limited(unknown-reset), 넘기면 ok 로 downgrade.
        if [ "$age_min" -lt "$UNKNOWN_WINDOW_MIN" ]; then
          state="limited(unknown-reset)"
        fi
      fi
    fi
  fi
  # jobs.log 자체가 없으면 조회 불가 = unknown.
  [ -f "$JOBS" ] || state="unknown"
  printf '%s %s\n' "$h" "$state"
done

# 한도 비대칭 기본값 — 이름 있는 설정값(SD-OPEN-3): env 로 교체 가능, 하드코드 금지.
printf 'bias %s\n' "${HARNESS_CAPACITY_BIAS:-claude}"
