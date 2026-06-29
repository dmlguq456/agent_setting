#!/usr/bin/env bash
# Toggle tracked/untracked workflow mode for the project containing cwd.
# The flag is session-scoped when a session id is provided.
set -euo pipefail

usage() {
  cat <<'EOF'
usage: workflow-toggle.sh [--cwd <dir>] [--session <id>] [--set toggle|tracked|untracked]

Toggles or sets the workflow bypass flag under .agent_reports/ or legacy
.claude_reports/.
EOF
}

CWD="$PWD"
SID="${AGENT_SESSION_ID:-${CLAUDE_CODE_SESSION_ID:-}}"
SET_MODE="toggle"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --cwd)
      [ "$#" -ge 2 ] || { echo "workflow-toggle: --cwd requires a dir" >&2; exit 64; }
      CWD=$2
      shift 2
      ;;
    --session)
      [ "$#" -ge 2 ] || { echo "workflow-toggle: --session requires an id" >&2; exit 64; }
      SID=$2
      shift 2
      ;;
    --set)
      [ "$#" -ge 2 ] || { echo "workflow-toggle: --set requires a mode" >&2; exit 64; }
      case "$2" in
        toggle|tracked|untracked) SET_MODE=$2 ;;
        *) echo "workflow-toggle: unknown mode: $2" >&2; exit 64 ;;
      esac
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "workflow-toggle: unknown argument: $1" >&2
      usage >&2
      exit 64
      ;;
  esac
done

d=$CWD
root=""
reports_dir=""
for _ in $(seq 1 40); do
  [ -d "$d/.agent_reports" ] && { root=$d; reports_dir=.agent_reports; break; }
  [ -d "$d/.claude_reports" ] && { root=$d; reports_dir=.claude_reports; break; }
  { [ "$d" = "/" ] || [ "$d" = "$HOME" ]; } && break
  d=$(dirname "$d")
done

if [ -z "$root" ]; then
  echo "No .agent_reports/.claude_reports ancestor found; workflow mode is not project-scoped."
  exit 0
fi

flag="$root/$reports_dir/.untracked"
[ -n "$SID" ] && flag="$flag.$SID"

case "$SET_MODE" in
  tracked)
    rm -f "$flag"
    ;;
  untracked)
    touch "$flag"
    ;;
  toggle)
    if [ -f "$flag" ]; then
      rm -f "$flag"
      SET_MODE=tracked
    else
      touch "$flag"
      SET_MODE=untracked
    fi
    ;;
esac

case "$SET_MODE" in
  tracked)
    echo "📌 tracked mode — workflow gates are active for this session."
    ;;
  untracked)
    echo "⚡ untracked mode — workflow gates are bypassed for this session. [$root]"
    ;;
esac
