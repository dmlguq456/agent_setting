#!/usr/bin/env sh
# Print the one writable artifact root for a project.
#
# Linked task worktrees are source-only execution surfaces. Their tracked
# .agent_reports snapshot is never selected as a write target. An explicit
# absolute AGENT_ARTIFACT_ROOT wins; otherwise Git projects use the primary
# worktree (the first `git worktree list --porcelain` entry). Non-Git projects
# retain upward discovery from the supplied cwd.
set -eu

physical_dir() {
  candidate=$1
  [ -d "$candidate" ] || return 1
  (CDPATH= cd -- "$candidate" && pwd -P)
}

physical_path() {
  candidate=$1
  if [ -d "$candidate" ]; then
    physical_dir "$candidate"
    return
  fi
  parent=$(dirname "$candidate")
  leaf=$(basename "$candidate")
  parent=$(physical_dir "$parent") || return 1
  printf '%s/%s\n' "$parent" "$leaf"
}

if [ -n "${AGENT_ARTIFACT_ROOT:-}" ]; then
  case "$AGENT_ARTIFACT_ROOT" in
    /*) ;;
    *)
      echo "artifact-root: AGENT_ARTIFACT_ROOT must be an absolute path" >&2
      exit 64
      ;;
  esac
  physical_path "$AGENT_ARTIFACT_ROOT" || {
    echo "artifact-root: parent directory does not exist: $AGENT_ARTIFACT_ROOT" >&2
    exit 66
  }
  exit 0
fi

start="${1:-$PWD}"
start=$(physical_dir "$start") || {
  echo "artifact-root: directory does not exist: $start" >&2
  exit 66
}

if command -v git >/dev/null 2>&1 \
  && git -C "$start" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  primary=$(git -C "$start" worktree list --porcelain 2>/dev/null \
    | awk '$1=="worktree"{print substr($0,10); exit}')
  [ -n "$primary" ] || primary=$(git -C "$start" rev-parse --show-toplevel)
  primary=$(physical_dir "$primary")
  if [ -d "$primary/.agent_reports" ]; then
    physical_dir "$primary/.agent_reports"
  elif [ -d "$primary/.claude_reports" ]; then
    physical_dir "$primary/.claude_reports"
  else
    printf '%s/.agent_reports\n' "$primary"
  fi
  exit 0
fi

d=$start
while :; do
  if [ -d "$d/.agent_reports" ]; then
    physical_dir "$d/.agent_reports"
    exit 0
  fi
  if [ -d "$d/.claude_reports" ]; then
    physical_dir "$d/.claude_reports"
    exit 0
  fi
  [ "$d" = "/" ] && break
  parent=$(dirname "$d")
  [ "$parent" = "$d" ] && break
  d=$parent
done
printf '%s/.agent_reports\n' "$start"
