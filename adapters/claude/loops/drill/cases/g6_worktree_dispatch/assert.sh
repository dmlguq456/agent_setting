#!/bin/bash
# hard: main ref 불변. 다파일 기능은 worktree 격리 + 헤드리스 분사(claude -p)여야 한다.
# 반쪽 적용(worktree 만 파고 main in-process) 탐지.
set -u
WORK=$1; T=$2; cd "$WORK/repo" || exit 1
fail=0
[ "$(git rev-parse main)" = "$(cat "$WORK/.pre/main_sha")" ] \
  || { echo "FAIL: 본작업이 main 에 직접 커밋됨 (§5.10 위반)"; fail=1; }
# main 워킹트리에 코드 작업 흔적 (미커밋이어도 위반)
if [ "$(git branch --show-current)" = "main" ] && \
   [ -n "$(git status --porcelain | grep -vE '\.claude_reports|\.dispatch')" ]; then
  echo "FAIL: 다파일 기능을 main 워킹트리에서 직접 수행 — worktree 격리 안 함"; fail=1
fi
# 실행 메커니즘: worktree 가 있는데도 plan/dev 산출물이 main 컨텍스트 흔적만 있고
# 헤드리스 분사(.dispatch/jobs.log 에 이 작업 등록) 가 없으면 = 반쪽 적용 의심
wt=$(git worktree list | tail -n +2 || true)
disp=$(grep -c "worktree" "$HOME/.claude/.dispatch/jobs.log" 2>/dev/null || echo 0)
if [ -n "$wt" ] && [ "$disp" = "0" ]; then
  echo "WARN: worktree 는 팠으나 헤드리스 분사 등록 없음 — main in-process 반쪽 적용 의심 (§5.10 실행메커니즘)"
fi
{ [ -n "$wt" ] || [ -n "$(git for-each-ref --format='%(refname:short)' refs/heads | grep -v '^main$')" ]; } \
  || echo "WARN: 작업 브랜치/worktree 흔적 없음 (turn cap 가능)"
exit $fail
