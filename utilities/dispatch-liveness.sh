#!/usr/bin/env bash
# dispatch-liveness — 분사(headless claude -p) job 의 stealth-death 결정론 점검.
#   문제: hung/crashed headless 는 exit 안 함 → 완료 알림 안 옴 → 메인 무한 대기 (2026-06-16 5h 사고).
#   §0.5 결정론-우선: "vigilant 하게 기억" 대신 이 스크립트가 jobs.log 의 open 분사를 판정.
#   신호 = 세션 transcript(`projects/<enc-cwd>/*.jsonl`) mtime — hang/death 하면 transcript 가 멈춘다
#   (pgrep 경로매칭은 흔한 path 가 무관 프로세스에 걸려 false-alive → 불채택).
#   사용: 분사 후 대기 자리에서 실행. SUSPECT/DEAD 면 transcript·dispatch 로그 진단 → 수확/재분사 (대기 X).
#   OPERATIONS §5.10 분사 가드. exit 3 = stealth-death 의심 1+.
set -uo pipefail
AGENT_HOME="${AGENT_HOME:-${CLAUDE_HOME:-$HOME/.claude}}"
JOBS="${1:-$AGENT_HOME/.dispatch/jobs.log}"
STALE_MIN="${DISPATCH_STALE_MIN:-15}"   # transcript 가 N분+ 멈췄으면 hang/death 의심
PROJ="$AGENT_HOME/projects"
[ -f "$JOBS" ] || { echo "(jobs.log 없음: $JOBS)"; exit 0; }

now=$(date +%s); alive=0; suspect=0; open_n=0
while IFS=$'\t' read -r ts status repo wt slug pipe || [ -n "${ts:-}" ]; do
  [ "${status:-}" = "open" ] || continue
  open_n=$((open_n + 1))
  enc=$(printf '%s' "${wt:-}" | sed 's#[/._]#-#g')
  dir="$PROJ/$enc"
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
