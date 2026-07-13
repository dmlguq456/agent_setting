#!/usr/bin/env bash
# dispatch-liveness — adapter-specific headless job 의 stealth-death 결정론 점검.
#   문제: hung/crashed headless 는 exit 안 함 → 완료 알림 안 옴 → 메인 무한 대기 (2026-06-16 5h 사고).
#   §0.5 결정론-우선: "vigilant 하게 기억" 대신 이 스크립트가 jobs.log 의 open 분사를 판정.
#   신호 1순위 = row 의 `pid=`(wrapper 가 launch 직후 기록) — /proc/<pid> 실존 + cmdline 'claude' 대조
#   (pid-reuse 가드). 공유-worktree 자식은 conductor 자신의 Bash 활동이 같은 transcript 디렉토리를
#   신선하게 유지해 mtime 단독 판정이 "이미 종료한 자식"을 ALIVE 로 오탐한다(2026-07-13 실측, ~50분
#   수확 지연) — pid 신호가 이 aliasing 을 닫는다. pid 종료+row open = EXITED(수확 필요).
#   신호 2순위(fallback, pid 없는 legacy·타 하네스 row) = 세션 transcript(`projects/<enc-cwd>/*.jsonl`)
#   mtime — hang/death 하면 transcript 가 멈춘다 (pgrep 경로매칭은 흔한 path 가 무관 프로세스에 걸려
#   false-alive → 불채택; pid= 는 경로매칭이 아니라 wrapper 가 기록한 정확한 자식 pid 라 이 함정 없음).
#   사용: 분사 후 대기 자리에서 실행. SUSPECT/DEAD/EXITED 면 transcript·dispatch 로그 진단 → 수확/재분사 (대기 X).
#   OPERATIONS §5.10 분사 가드. exit 3 = stealth-death 의심 또는 미수확 종료 1+.
set -uo pipefail
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
AGENT_HOME="${AGENT_HOME:-$("$SCRIPT_DIR/agent-home.sh")}"
JOBS="${1:-${AGENT_DISPATCH_JOBS:-$AGENT_HOME/.dispatch/jobs.log}}"
STALE_MIN="${DISPATCH_STALE_MIN:-15}"   # transcript 가 N분+ 멈췄으면 hang/death 의심
# runtime-root(harness-layer-sync §4.1 · HLS-6): 런타임이 세션 transcript/state 를 쓰는 곳은
# AGENT_HOME(하네스 소스 repo)이 아니다. Claude 세션 transcript 는 ~/.claude/projects/ 에 있어
# $AGENT_HOME/projects 로는 못 봐 살아있는 non-profile job 을 DEAD 오탐한다(2026-07-09 실측).
# Claude=${CLAUDE_CONFIG_DIR:-$HOME/.claude}; 타 런타임은 DISPATCH_RUNTIME_ROOT 로 재정의
# (Codex=$CODEX_HOME · OpenCode=~/.config/opencode). profile 경로(아래 homes/<slug>.<name>/)는
# 이미 runtime-root 격리라 이 계약과 정합 — 건드리지 않는다.
RUNTIME_ROOT="${DISPATCH_RUNTIME_ROOT:-${CLAUDE_CONFIG_DIR:-$HOME/.claude}}"
PROJ="$RUNTIME_ROOT/projects"
LOG_DIR="$AGENT_HOME/.dispatch/logs"
# SD-15 (OPERATIONS §5.10 ⑨): open row 의 dispatch 로그가 limit/auth 즉사 패턴을 보이면
# 그 사유를 DEAD 판정에 쓴다 (wrapper 워치 창이 놓쳤거나 launch 후 뒤늦게 죽은 자식). 패턴
# 목록은 dispatch-headless.py 의 DEATH_PATTERNS 와 동기 유지(의도적 복제).
LIMIT_RE='hit your (session|usage) limit|session limit reached|usage limit reached|weekly limit|rate limit|[^0-9]429[^0-9]|invalid api key|authentication_error|not logged in|please run /login|unauthorized|[^0-9]401[^0-9]|credit balance is too low|insufficient (credit|quota|funds)'

# SD-15b (OPERATIONS §8.6.1): 로그-패턴 DEAD 판정을 앵커링한다. 과거엔 tail -c 8000 전체를
# LIMIT_RE 로 훑어, 정상 완주 conductor 의 최종 보고문이 limit 을 _주제로_ 서술하기만 해도 DEAD
# 오탐이 났다(sd15-adapter-parity 실측). 실제 CLI limit-사망은 로그 _말미_ 에 짧은 단독 에러 라인
# (예: "You've hit your session limit · resets 3pm")을 남기고 exit 하므로, 매치를 (a) 말미 소수
# 라인 + (b) 짧은 단독 라인 형태로 한정한다. 완주 신호(신선 transcript)와의 결합은 아래 루프가 맡는다
# — transcript 가 신선하면 이 스캔을 아예 부르지 않는다(완주면 DEAD 배제).
scan_log_death() {  # $1=slug ; 짧은 말미 death 라인이 있으면 그 로그 경로를 출력하고 return 0, 아니면 return 1.
  _slug=$1
  [ -n "$_slug" ] || return 1
  for lf in "$LOG_DIR/${_slug}."*.log; do
    [ -f "$lf" ] || continue
    # 말미 40줄 중 비어있지 않은 마지막 3줄만, 그리고 매치 라인이 짧을(≤200) 때만 death 로 인정.
    hit=$(tail -n 40 "$lf" 2>/dev/null | awk 'NF' | tail -n 3 \
      | grep -Ei "$LIMIT_RE" | awk 'length($0) <= 200 { print; exit }')
    [ -n "$hit" ] && { printf '%s' "$lf"; return 0; }
  done
  return 1
}

[ -f "$JOBS" ] || { echo "(jobs.log 없음: $JOBS)"; exit 0; }

now=$(date +%s); alive=0; suspect=0; open_n=0
while IFS=$'\t' read -r ts status repo wt slug pipe || [ -n "${ts:-}" ]; do
  [ "${status:-}" = "open" ] || continue
  open_n=$((open_n + 1))
  # ── 1순위: pid 신호 (wrapper 기록 — 공유-worktree transcript aliasing 무관) ──
  pid=$(printf '%s' "$pipe" | tr ',' '\n' | sed -n 's/^pid=//p' | head -1)
  [ -d /proc ] || pid=""   # /proc 없는 플랫폼은 fallback (mtime 판정)
  if [ -n "$pid" ] && [ -d "/proc/$pid" ] \
     && tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null | grep -q 'claude'; then
    echo "ALIVE      ${slug:-?}  (pid $pid 실행 중)"
    alive=$((alive + 1)); continue
  fi
  if [ -n "$pid" ]; then
    # pid 종료 + row open = 정상 완주(미수확) 또는 사망 — limit 사유 스캔으로 구분 표기.
    if log_hit=$(scan_log_death "$slug"); then
      echo "⚠️ DEAD     ${slug:-?}  — 로그 limit/auth 패턴 ($log_hit)  [open: $ts]"
    else
      echo "⚠️ EXITED   ${slug:-?}  — pid $pid 종료·row 미마감 (dispatch 로그 tail 로 verdict 수확)  [open: $ts]"
    fi
    suspect=$((suspect + 1)); continue
  fi
  # ── 2순위(fallback): transcript-mtime 판정 (pid 없는 legacy·타 하네스 row) ──
  enc=$(printf '%s' "${wt:-}" | sed 's#[/._]#-#g')
  name=""
  case "$pipe" in *profile=*) name=${pipe##*profile=}; name=${name%%,*};; esac
  if [ -n "$name" ]; then
    dir="$AGENT_HOME/.dispatch/homes/${slug}.${name}/projects/$enc"
  else
    dir="$PROJ/$enc"
  fi
  newest=$(ls -t "$dir"/*.jsonl 2>/dev/null | head -1)
  if [ -z "$newest" ]; then
    # transcript 부재 — launch 전 즉사했거나 아예 안 뜬 자식. 앵커링된 로그 스캔으로 limit/auth
    # 사유를 붙이고, 없으면 generic DEAD (SD-15b: 부재 자체가 death 신호, 스캔은 사유 판정용).
    if log_hit=$(scan_log_death "$slug"); then
      echo "⚠️ DEAD     ${slug:-?}  — 로그 limit/auth 패턴 ($log_hit)  [open: $ts]"
    else
      echo "⚠️ DEAD     ${slug:-?}  — 세션 transcript 없음 ($dir)  [open: $ts]"
    fi
    suspect=$((suspect + 1)); continue
  fi
  mt=$(stat -c %Y "$newest" 2>/dev/null || echo 0)
  age=$(( (now - mt) / 60 ))
  if [ "$age" -le "$STALE_MIN" ]; then
    # SD-15b: 신선 transcript = 완주/활성 신호 → 로그 본문의 limit prose 매치가 있어도 DEAD 배제.
    echo "ALIVE      ${slug:-?}  (transcript ${age}m 전 갱신)"
    alive=$((alive + 1))
  else
    # stale — hang, 또는 limit-사망 후 정지. 앵커링된 로그 스캔으로 확정적 limit/auth 사유를 붙이고,
    # 없으면 SUSPECT(mtime 정지).
    if log_hit=$(scan_log_death "$slug"); then
      echo "⚠️ DEAD     ${slug:-?}  — 로그 limit/auth 패턴 ($log_hit)  [open: $ts]"
    else
      echo "⚠️ SUSPECT  ${slug:-?}  — transcript ${age}m 정지 (hang/death 의심)  [open: $ts]"
    fi
    suspect=$((suspect + 1))
  fi
done < "$JOBS"

echo "— open $open_n · alive $alive · suspect/dead/exited $suspect"
if [ "$suspect" -gt 0 ]; then
  echo "→ SUSPECT/DEAD/EXITED: transcript tail·dispatch 로그 확인 → 수확 또는 재분사. 완료 알림 무한 대기 금지."
  exit 3
fi
exit 0
