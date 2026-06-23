#!/bin/sh
# PreToolUse(Edit|Write|MultiEdit|NotebookEdit) — merge/rebase/cherry-pick 진행 중인
# git repo 의 파일 편집을 DENY (OPERATIONS §5.9 의 edit-time 하드 강제).
# 직접 편집 경로(ceremony 비경유)도 커버 — golden g2 (2026-06-11) 가 잡은 구멍.
# 탈출구: 사용자가 _명시적으로_ 충돌 해결을 요청한 경우에만 $GITDIR/CLAUDE_MERGE_EDIT_OK
# 를 만들고 진행, 작업 후 삭제. Claude 자가 판단 생성 금지 (artifact-guard untracked 와 동일 convention).
# POSIX sh, no jq.

input=$(cat 2>/dev/null)
[ -z "$input" ] && exit 0

fp=$(printf '%s' "$input" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"//; s/"$//')
[ -z "$fp" ] && exit 0

dir=$(dirname "$fp")
# dirname 이 아직 없으면 존재하는 최근접 조상으로 올라간다 — merge/rebase 중 없는 하위폴더
# 신규 write 가 git 판정을 건너뛰고 우회하던 구멍을 메움 (codex #7, 2026-06-22).
while [ ! -d "$dir" ] && [ "$dir" != "/" ] && [ "$dir" != "." ]; do dir=$(dirname "$dir"); done
[ -d "$dir" ] || exit 0
gd=$(git -C "$dir" rev-parse --git-dir 2>/dev/null) || exit 0
case "$gd" in /*) ;; *) gd="$dir/$gd" ;; esac

op=""
[ -f "$gd/MERGE_HEAD" ] && op="merge"
[ -d "$gd/rebase-merge" ] || [ -d "$gd/rebase-apply" ] && op="rebase"
[ -f "$gd/CHERRY_PICK_HEAD" ] && op="cherry-pick"
# detached HEAD — 브랜치 없이 커밋에 직접 올라탄 상태. CLAUDE.md §0(C)·§5.9 가 STOP+hook
# 강제로 약속한 자리인데 종전 hook 은 안 막았다 (codex #6, 2026-06-22).
[ -z "$op" ] && ! git -C "$dir" symbolic-ref --quiet HEAD >/dev/null 2>&1 && op="detached-HEAD"
[ -z "$op" ] && exit 0

# 명시 요청 탈출구
[ -f "$gd/CLAUDE_MERGE_EDIT_OK" ] && exit 0

printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s 진행 중인 repo — 편집·커밋 STOP, 상태 보고가 기본 (OPERATIONS §5.9). 충돌 해소·머지 완결을 임의로 하지 말 것. 사용자가 명시적으로 충돌 해결을 요청한 경우에만 touch %s/CLAUDE_MERGE_EDIT_OK 후 진행하고 작업 후 삭제."}}\n' "$op" "$gd"
exit 0
