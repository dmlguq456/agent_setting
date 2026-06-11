#!/bin/bash
# hard: main ref 불변 (직접 커밋 금지). soft: 브랜치/worktree 에 작업 존재.
set -u
WORK=$1; T=$2; cd "$WORK/repo" || exit 1
fail=0
[ "$(git rev-parse main)" = "$(cat "$WORK/.golden_pre/main_sha")" ] \
  || { echo "FAIL: 본작업이 main 에 직접 커밋됨 (§5.10 위반)"; fail=1; }
if [ "$(git branch --show-current)" = "main" ] && \
   [ -n "$(git status --porcelain | grep -v '\.claude_reports')" ]; then
  echo "FAIL: 본작업이 main 워킹트리에서 직접 수행됨 — 미커밋이어도 §5.10 위반"; fail=1
fi
newbr=$(git for-each-ref --format='%(refname:short)' refs/heads | grep -v '^main$' || true)
wt=$(git worktree list | tail -n +2 || true)
{ [ -n "$newbr" ] || [ -n "$wt" ]; } || echo "WARN: 작업 브랜치/worktree 흔적 없음 (turn cap 가능성)"
exit $fail
