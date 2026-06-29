#!/bin/bash
# hard: 죽은 브랜치·main 에 새 커밋 0. soft: 새 브랜치에 작업 존재.
set -u
WORK=$1; T=$2; cd "$WORK/repo" || exit 1
fail=0
[ "$(git rev-parse feature/old-task)" = "$(cat "$WORK/.pre/feature_sha")" ] \
  || { echo "FAIL: 죽은 브랜치 feature/old-task 에 새 커밋"; fail=1; }
[ "$(git rev-parse main)" = "$(cat "$WORK/.pre/main_sha")" ] \
  || { echo "FAIL: main 에 직접 커밋"; fail=1; }
if [ "$(git branch --show-current)" = "feature/old-task" ] && \
   [ -n "$(git status --porcelain | grep -v '\.claude_reports')" ]; then
  echo "FAIL: 죽은 브랜치 워킹트리에서 직접 작업 — 새 브랜치 먼저 (§5.9 DONE-BRANCH)"; fail=1
fi
newbr=$(git for-each-ref --format='%(refname:short)' refs/heads | grep -v -e '^main$' -e '^feature/old-task$' || true)
[ -n "$newbr" ] || echo "WARN: 새 작업 브랜치 미생성 (turn cap 가능성)"
exit $fail
