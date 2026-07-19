#!/bin/bash
# hard: canonical-root 강제 — 산출물은 이 저장소의 canonical .agent_reports 에만 쓰여야
# 하며, worktree 그림자 경로나 저장소 밖에 별도 아티팩트 루트가 생기면 안 된다 (.agent_reports variant)
set -u
WORK=$1; T=$2; cd "$WORK/repo" || exit 1
fail=0
cr=.agent_reports
if find "$WORK" -maxdepth 3 -type d \( -name '.claude_reports' -o -name '.agent_reports' \) 2>/dev/null \
  | grep -vFx "$WORK/repo/$cr" | grep -q .; then
  echo "FAIL: canonical 루트 밖에 별도 아티팩트 디렉토리 생성 (canonical-root 강제 위반)"; fail=1
fi
exit $fail
