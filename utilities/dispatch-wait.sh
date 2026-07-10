#!/usr/bin/env sh
# dispatch-wait — SD-14 one-shot 대기 계약 헬퍼 (OPERATIONS §5.10 one-shot 대기 계약).
#   문제: adapter headless main(conductor 포함)은 one-shot 프로세스 — turn 종료 = 프로세스 종료.
#   따라서 스테이지를 분사한 conductor 는 완료 알림 대기로 turn 을 끝낼 수 없고(알림은 죽은
#   프로세스에 안 옴), 같은 turn 안에서 스테이지 종료를 능동 폴링해야 한다.
#   본 헬퍼는 liveness 를 재구현하지 않고 dispatch-liveness.sh 를 재사용해 판정만 감싼다.
#
#   사용: dispatch-wait.sh [--parent <self-slug>] [--jobs <path>] [--interval <s>] [--max <s>]
#     --parent  내 slug (AGENT_DISPATCH_SELF_SLUG). 주면 jobs.log 의 open row 중 parent=<slug>
#               자식만 대상으로 판정. 생략하면 모든 open row.
#     --jobs    jobs.log 경로 (default $AGENT_HOME/.dispatch/jobs.log, liveness 와 동일 해석).
#     --interval 폴 간격초 (default 20).
#     --max     이 한 호출의 최대 대기초 (default 120, 상한 600 — 단일 Bash timeout 존중).
#
#   exit 0 = 대상 자식이 모두 종료(open 아님) → 수확하라.
#   exit 2 = 아직 살아있음, --max 도달 → 재호출하라(반복-호출 폴 형태; conductor 의 다음 Bash 가 이어감).
#   exit 3 = SUSPECT/DEAD 자식 있음 → 대기 금지, transcript tail·dispatch 로그로 진단→수확/재분사.
#   각 iteration 한 줄 status 출력. background/nohup 없음(스테이지-워커 의무 — 동기 폴만).
#   SD-15 (OPERATIONS §5.10 ⑨): DEAD 판정은 dispatch-liveness 재사용이라, 자식 dispatch
#   로그의 limit/auth 즉사 패턴도 자동으로 exit 3 근거가 된다(transcript-mtime 단독 의존 탈피).
set -u   # POSIX sh(dash)에는 pipefail 없음 — liveness 재사용이라 pipe 상태 의존 없음.

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
AGENT_HOME="${AGENT_HOME:-$("$SCRIPT_DIR/agent-home.sh")}"
LIVENESS="$SCRIPT_DIR/dispatch-liveness.sh"

PARENT=""
JOBS=""
INTERVAL=20
MAX=120
while [ $# -gt 0 ]; do
  case "$1" in
    --parent) PARENT="${2:-}"; shift 2 ;;
    --jobs) JOBS="${2:-}"; shift 2 ;;
    --interval) INTERVAL="${2:-20}"; shift 2 ;;
    --max) MAX="${2:-120}"; shift 2 ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "dispatch-wait: unknown arg '$1'" >&2; exit 64 ;;
  esac
done
[ -n "$JOBS" ] || JOBS="$AGENT_HOME/.dispatch/jobs.log"
# 상한 클램프: 단일 Bash timeout 안에 끝나도록.
[ "$MAX" -gt 600 ] 2>/dev/null && MAX=600
[ "$INTERVAL" -ge 1 ] 2>/dev/null || INTERVAL=20

# jobs.log 없으면 대기할 자식도 없음 → 수확 가능.
if [ ! -f "$JOBS" ]; then
  echo "(jobs.log 없음: $JOBS) — 열린 자식 없음"
  exit 0
fi

# open 자식 row 추출: --parent 주면 pipe 의 parent=<slug> 키가 정확히 일치하는 open row 만.
open_children() {
  awk -F'\t' -v slug="$PARENT" '
    ($2=="open") {
      if (slug=="") { print; next }
      n=split($6, kv, ",")
      for (i=1;i<=n;i++) { if (kv[i]=="parent=" slug) { print; next } }
    }' "$JOBS"
}

elapsed=0
while :; do
  rows=$(open_children)
  # 빈 문자열이면 grep -c 가 아니라 직접 카운트 (빈 줄 오탐 방지)
  if [ -z "$rows" ]; then
    if [ -n "$PARENT" ]; then
      echo "✓ parent=$PARENT 의 열린 자식 없음 — 수확 가능 (exit 0)"
    else
      echo "✓ 열린 자식 없음 — 수확 가능 (exit 0)"
    fi
    exit 0
  fi
  n=$(printf '%s\n' "$rows" | grep -c .)

  # 대상 자식만 담은 임시 jobs 로 liveness 재사용 (exit 3 이 내 자식만 반영하도록).
  tmp=$(mktemp)
  printf '%s\n' "$rows" > "$tmp"
  live_out=$(AGENT_HOME="$AGENT_HOME" "$LIVENESS" "$tmp" 2>&1)
  live_rc=$?
  rm -f "$tmp"

  if [ "$live_rc" -eq 3 ]; then
    echo "⚠️ SUSPECT/DEAD 자식 있음 (open $n) — 대기 금지, 진단하라 (exit 3)"
    printf '%s\n' "$live_out"
    exit 3
  fi

  if [ "$elapsed" -ge "$MAX" ]; then
    echo "… 자식 $n개 아직 실행 중 (${elapsed}s 폴, max ${MAX}s 도달) — 재호출하라 (exit 2)"
    exit 2
  fi

  echo "… 자식 $n개 ALIVE — ${INTERVAL}s 후 재폴 (경과 ${elapsed}s/${MAX}s)"
  sleep "$INTERVAL"
  elapsed=$((elapsed + INTERVAL))
done
