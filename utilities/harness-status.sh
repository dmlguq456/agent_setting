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
  porcelain=$(git -C "$cwd" status --porcelain 2>/dev/null || true)
  git_dirty_tracked=$(printf '%s\n' "$porcelain" | awk 'NF && $1!="??"{c++} END{print c+0}')
  git_untracked=$(printf '%s\n' "$porcelain" | awk '$1=="??"{c++} END{print c+0}')
  git_dirty_total=$((git_dirty_tracked + git_untracked))
  if [ "$git_dirty_total" -gt 0 ]; then
    printf 'git_dirty=1\n'
  else
    printf 'git_dirty=0\n'
  fi
  printf 'git_dirty_tracked=%s\n' "$git_dirty_tracked"
  printf 'git_untracked=%s\n' "$git_untracked"
  printf 'git_dirty_total=%s\n' "$git_dirty_total"

  worktree_count=$(git -C "$cwd" worktree list --porcelain 2>/dev/null | awk '$1=="worktree"{c++} END{print c+0}')
  printf 'git_worktree_count=%s\n' "${worktree_count:-0}"
  if [ "${worktree_count:-0}" -gt 1 ] 2>/dev/null; then
    printf 'git_extra_worktrees=%s\n' $((worktree_count - 1))
  else
    printf 'git_extra_worktrees=0\n'
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

  # Upstream divergence + dead-branch risk: a branch with an upstream and zero
  # commits ahead is fully merged/up-to-date — editing on it directly is the
  # DONE-BRANCH hazard (branch first). Reported so adapters can warn before edits.
  upstream=$(git -C "$cwd" rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)
  if [ -n "$upstream" ]; then
    printf 'git_upstream=%s\n' "$upstream"
    counts=$(git -C "$cwd" rev-list --left-right --count "$upstream...HEAD" 2>/dev/null || true)
    git_behind=$(printf '%s' "$counts" | awk '{print $1+0}')
    git_ahead=$(printf '%s' "$counts" | awk '{print $2+0}')
    printf 'git_ahead=%s\n' "${git_ahead:-0}"
    printf 'git_behind=%s\n' "${git_behind:-0}"
    # DONE-BRANCH risk: a non-default topic branch fully merged (0 ahead) is dead —
    # branch first before editing. Default branches up-to-date are not "done".
    case "$branch" in
      main|master|develop|trunk|"") is_default_branch=1 ;;
      *) is_default_branch=0 ;;
    esac
    if [ "${git_ahead:-0}" = "0" ] && [ "$git_operation" = "none" ] && [ "$is_default_branch" = "0" ]; then
      printf 'git_branch_done=1\n'
    else
      printf 'git_branch_done=0\n'
    fi
  else
    printf 'git_upstream=none\n'
    printf 'git_branch_done=0\n'
  fi
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

# Open headless dispatch jobs (portable .dispatch/jobs.log registry; tab fields:
# ts, state, repo, worktree, slug, pipe). Surfaces in-flight background work that
# native status footers do not cover. Override the registry path with
# AGENT_DISPATCH_JOBS.
self_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
status_home=${AGENT_HOME:-}
if [ -z "$status_home" ] || [ ! -f "$status_home/core/CORE.md" ]; then
  status_home=$(CDPATH= cd -- "$self_dir/.." && pwd)
fi
jobs_log=${AGENT_DISPATCH_JOBS:-$status_home/.dispatch/jobs.log}
headless_open=0
headless_slugs=""
if [ -f "$jobs_log" ]; then
  headless_open=$(awk -F '\t' 'NF==6 && $2=="open"{c++} END{print c+0}' "$jobs_log")
  headless_slugs=$(awk -F '\t' 'NF==6 && $2=="open"{printf "%s%s", sep, $5; sep=","}' "$jobs_log")
fi
printf 'headless_open_jobs=%s\n' "$headless_open"
if [ -n "$headless_slugs" ]; then
  printf 'headless_open_slugs=%s\n' "$headless_slugs"
fi

printf 'note=read-only snapshot; runtime-native status UI remains authoritative for model/context/token/session fields\n'
