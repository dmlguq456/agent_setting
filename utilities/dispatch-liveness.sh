#!/usr/bin/env bash
# dispatch-liveness — adapter-specific headless job 의 stealth-death 결정론 점검.
#   문제: hung/crashed headless 는 exit 안 함 → 완료 알림 안 옴 → 메인 무한 대기 (2026-06-16 5h 사고).
#   §0.5 결정론-우선: "vigilant 하게 기억" 대신 이 스크립트가 jobs.log 의 open 분사를 판정.
#   신호 = 세션 transcript(`projects/<enc-cwd>/*.jsonl`) mtime — hang/death 하면 transcript 가 멈춘다
#   (pgrep 경로매칭은 흔한 path 가 무관 프로세스에 걸려 false-alive → 불채택).
#   사용: 분사 후 대기 자리에서 실행. SUSPECT/DEAD 면 transcript·dispatch 로그 진단 → 수확/재분사 (대기 X).
#   OPERATIONS §5.10 분사 가드. exit 3 = stealth-death 의심 1+.
set -uo pipefail
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
AGENT_HOME="${AGENT_HOME:-$("$SCRIPT_DIR/agent-home.sh")}"
JOBS="${1:-$AGENT_HOME/.dispatch/jobs.log}"
STALE_MIN="${DISPATCH_STALE_MIN:-15}"   # transcript 가 N분+ 멈췄으면 hang/death 의심
# runtime-root(harness-layer-sync §4.1 · HLS-6): 런타임이 세션 transcript/state 를 쓰는 곳은
# AGENT_HOME(하네스 소스 repo)이 아니다. Claude 세션 transcript 는 ~/.claude/projects/ 에 있어
# $AGENT_HOME/projects 로는 못 봐 살아있는 non-profile job 을 DEAD 오탐한다(2026-07-09 실측).
# Claude=${CLAUDE_CONFIG_DIR:-$HOME/.claude}; 타 런타임은 DISPATCH_RUNTIME_ROOT 로 재정의
# (Codex=$CODEX_HOME · OpenCode=~/.config/opencode). profile 경로(아래 homes/<slug>.<name>/)는
# 이미 runtime-root 격리라 이 계약과 정합 — 건드리지 않는다.
RUNTIME_ROOT="${DISPATCH_RUNTIME_ROOT:-${CLAUDE_CONFIG_DIR:-$HOME/.claude}}"
PROJ="$RUNTIME_ROOT/projects"
[ -f "$JOBS" ] || { echo "(jobs.log 없음: $JOBS)"; exit 0; }

now=$(date +%s); alive=0; suspect=0; open_n=0
while IFS=$'\t' read -r ts status repo wt slug pipe || [ -n "${ts:-}" ]; do
  [ "${status:-}" = "open" ] || continue
  open_n=$((open_n + 1))
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
    echo "⚠️ DEAD     ${slug:-?}  — 세션 transcript 없음 ($dir)  [open: $ts]"
    suspect=$((suspect + 1)); continue
  fi
  mt=$(stat -c %Y "$newest" 2>/dev/null || echo 0)
  age=$(( (now - mt) / 60 ))
  if [ "$age" -le "$STALE_MIN" ]; then
    echo "ALIVE      ${slug:-?}  (transcript ${age}m 전 갱신)"
    alive=$((alive + 1))
  else
    echo "⚠️ SUSPECT  ${slug:-?}  — transcript ${age}m 정지 (hang/death 의심)  [open: $ts]"
    suspect=$((suspect + 1))
  fi
done < "$JOBS"

echo "— open $open_n · alive $alive · suspect/dead $suspect"
if [ "$suspect" -gt 0 ]; then
  echo "→ SUSPECT/DEAD: transcript tail·dispatch 로그 확인 → 수확 또는 재분사. 완료 알림 무한 대기 금지."
  exit 3
fi
exit 0
