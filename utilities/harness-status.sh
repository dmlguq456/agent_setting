#!/usr/bin/env sh
# Read-only harness status snapshot for runtime adapters.
set -eu

usage() {
  cat <<'EOF'
usage: harness-status.sh [cwd] [session-id]

Prints machine-readable harness-specific status signals. This is not a
replacement for runtime-native status UI; adapters use it to expose the
workflow, artifact, notes, and git-risk signals that native footers usually do
not cover.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

cwd=${1:-$PWD}
sid=${2:-agent-status}
adapter=${AGENT_ADAPTER:-portable}

printf 'adapter=%s\n' "$adapter"
printf 'runtime_surface=adapter-owned-harness-status\n'
printf 'status=ok\n'
printf 'cwd=%s\n' "$cwd"

project_root=""
if command -v git >/dev/null 2>&1 && git -C "$cwd" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  project_root=$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null || true)
fi

search_root=${project_root:-$cwd}
d=$search_root
artifact_root=""
artifact_kind=""
for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40; do
  if [ -d "$d/.agent_reports" ]; then
    artifact_root="$d/.agent_reports"
    artifact_kind=".agent_reports"
    break
  fi
  if [ -d "$d/.claude_reports" ]; then
    artifact_root="$d/.claude_reports"
    artifact_kind=".claude_reports"
    break
  fi
  [ "$d" = "/" ] && break
  [ "$d" = "$HOME" ] && break
  d=$(dirname "$d")
done

if [ -n "$artifact_root" ]; then
  printf 'artifact_root=%s\n' "$artifact_root"
  printf 'artifact_root_kind=%s\n' "$artifact_kind"
  printf 'artifact_root_exists=1\n'
else
  expected=${project_root:-$cwd}/.agent_reports
  printf 'artifact_root=%s\n' "$expected"
  printf 'artifact_root_kind=.agent_reports\n'
  printf 'artifact_root_exists=0\n'
fi

workflow_state=not-configured
untracked_flag=""
if [ -n "$artifact_root" ]; then
  workflow_state=tracked
  if [ -f "$artifact_root/.untracked.$sid" ]; then
    workflow_state=untracked
    untracked_flag="$artifact_root/.untracked.$sid"
  elif [ -f "$artifact_root/.untracked" ]; then
    workflow_state=untracked
    untracked_flag="$artifact_root/.untracked"
  fi
fi
printf 'workflow_state=%s\n' "$workflow_state"
if [ -n "$untracked_flag" ]; then
  printf 'workflow_flag=%s\n' "$untracked_flag"
fi

if [ -n "$project_root" ]; then
  printf 'git_repo=1\n'
  printf 'git_root=%s\n' "$project_root"
  branch=$(git -C "$cwd" symbolic-ref --short HEAD 2>/dev/null || true)
  if [ -n "$branch" ]; then
    printf 'git_branch=%s\n' "$branch"
    printf 'git_detached=0\n'
  else
    printf 'git_branch=DETACHED\n'
    printf 'git_detached=1\n'
  fi
  if [ -n "$(git -C "$cwd" status --porcelain 2>/dev/null || true)" ]; then
    printf 'git_dirty=1\n'
  else
    printf 'git_dirty=0\n'
  fi

  gitdir=$(git -C "$cwd" rev-parse --absolute-git-dir 2>/dev/null || git -C "$cwd" rev-parse --git-dir 2>/dev/null || true)
  case "$gitdir" in
    /*) ;;
    "") ;;
    *) gitdir="$project_root/$gitdir" ;;
  esac
  git_operation=none
  if [ -n "$gitdir" ]; then
    [ -f "$gitdir/MERGE_HEAD" ] && git_operation=merge
    if [ -d "$gitdir/rebase-merge" ] || [ -d "$gitdir/rebase-apply" ]; then
      git_operation=rebase
    fi
    [ -f "$gitdir/CHERRY_PICK_HEAD" ] && git_operation=cherry-pick
  fi
  printf 'git_operation=%s\n' "$git_operation"
else
  printf 'git_repo=0\n'
fi

sibling_worktree=0
sibling_slug=""
case "$cwd" in
  *-wt/*)
    sibling_worktree=1
    sibling_slug=${cwd#*-wt/}
    sibling_slug=${sibling_slug%%/*}
    ;;
esac
printf 'sibling_worktree=%s\n' "$sibling_worktree"
if [ -n "$sibling_slug" ]; then
  printf 'sibling_worktree_slug=%s\n' "$sibling_slug"
fi

notes_root=${AGENT_NOTES_ROOT:-${WORKLOG_NOTES_ROOT:-}}
board_app=${WORKLOG_BOARD_APP:-}
board_wt=${WORKLOG_BOARD_WT:-}
if [ -n "$notes_root" ]; then
  printf 'agent_notes_root=%s\n' "$notes_root"
  [ -d "$notes_root" ] && printf 'agent_notes_root_exists=1\n' || printf 'agent_notes_root_exists=0\n'
else
  printf 'agent_notes_root=unset\n'
  printf 'agent_notes_root_exists=0\n'
fi
if [ -n "$board_app" ]; then
  printf 'worklog_board_app=%s\n' "$board_app"
  [ -e "$board_app" ] && printf 'worklog_board_app_exists=1\n' || printf 'worklog_board_app_exists=0\n'
else
  printf 'worklog_board_app=unset\n'
  printf 'worklog_board_app_exists=0\n'
fi
if [ -n "$board_wt" ]; then
  printf 'worklog_board_wt=%s\n' "$board_wt"
  [ -e "$board_wt" ] && printf 'worklog_board_wt_exists=1\n' || printf 'worklog_board_wt_exists=0\n'
else
  printf 'worklog_board_wt=unset\n'
  printf 'worklog_board_wt_exists=0\n'
fi

printf 'note=read-only snapshot; runtime-native status UI remains authoritative for model/context/token/session fields\n'
