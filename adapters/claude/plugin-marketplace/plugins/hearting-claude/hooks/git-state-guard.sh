#!/bin/sh
# PreToolUse(Edit|Write|MultiEdit|NotebookEdit): deny file edits while a git
# repository is merging, rebasing, or cherry-picking (OPERATIONS §5.9).
# This also covers direct edit paths that bypass workflow ceremony.
# Escape hatch: only after the user explicitly requests conflict resolution,
# create $GITDIR/CLAUDE_MERGE_EDIT_OK, perform the work, then delete it. The
# agent must not create the marker on its own.
# POSIX sh, no jq. Also supports portable CLI mode:
#   git-state-guard.sh --file <path>

fp=""
hook_mode=1

if [ "$#" -gt 0 ]; then
  hook_mode=0
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --file)
        [ "$#" -ge 2 ] || { echo "git-state-guard: --file requires a path" >&2; exit 64; }
        fp="$2"; shift 2 ;;
      --help|-h)
        echo "usage: git-state-guard.sh --file <path>"
        exit 0 ;;
      *)
        echo "git-state-guard: unknown argument: $1" >&2
        exit 64 ;;
    esac
  done
else
  input=$(cat 2>/dev/null)
  [ -z "$input" ] && exit 0
  fp=$(printf '%s' "$input" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"//; s/"$//')
fi
[ -z "$fp" ] && exit 0

dir=$(dirname "$fp")
# If dirname does not exist, walk to the nearest existing ancestor so a write
# to a new subdirectory cannot bypass merge/rebase detection.
while [ ! -d "$dir" ] && [ "$dir" != "/" ] && [ "$dir" != "." ]; do dir=$(dirname "$dir"); done
[ -d "$dir" ] || exit 0
gd=$(git -C "$dir" rev-parse --git-dir 2>/dev/null) || exit 0
case "$gd" in /*) ;; *) gd="$dir/$gd" ;; esac

op=""
[ -f "$gd/MERGE_HEAD" ] && op="merge"
[ -d "$gd/rebase-merge" ] || [ -d "$gd/rebase-apply" ] && op="rebase"
[ -f "$gd/CHERRY_PICK_HEAD" ] && op="cherry-pick"
# Detached HEAD means the worktree points directly at a commit without a branch.
[ -z "$op" ] && ! git -C "$dir" symbolic-ref --quiet HEAD >/dev/null 2>&1 && op="detached-HEAD"
[ -z "$op" ] && exit 0

# Explicit-request escape hatch.
[ -f "$gd/CLAUDE_MERGE_EDIT_OK" ] && exit 0

reason="$op is in progress in this repository. Stop edits and commits and report the state (OPERATIONS §5.9). Do not resolve conflicts or complete the operation without an explicit user request. After such a request, touch $gd/CLAUDE_MERGE_EDIT_OK, perform the work, then remove the marker."
if [ "$hook_mode" -eq 1 ]; then
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$reason"
  exit 0
fi

printf '⛔ %s\n' "$reason" >&2
exit 2
