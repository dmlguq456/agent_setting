#!/bin/sh
# PostToolUse(Read): write a session marker after prd.md is actually read.
# Portable CLI: spec-read-marker.sh --file <prd.md> [--session <id>] [--agent-home <dir>]
# spec-skill-gate.sh uses the marker as evidence of a real read, not a quotation.
# The marker stores prd.md mtime at read time for later drift comparison. POSIX sh, no jq.

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
AGENT_HOME="${AGENT_HOME:-$("$SCRIPT_DIR/../utilities/agent-home.sh")}"
ARTIFACT_ROOT_RESOLVER="$SCRIPT_DIR/../utilities/artifact-root.sh"

usage() {
  cat <<'EOF'
usage: spec-read-marker.sh --file <prd.md> [--session <id>] [--agent-home <dir>]

Without arguments, reads Claude hook JSON from stdin.
EOF
}

mark_read() {
  fp=$1
  sid=$2

  case "$fp" in
    /*) ;;
    *) fp="$PWD/$fp" ;;
  esac

  case "$fp" in
    */.agent_reports/spec/prd.md) ;;
    */.claude_reports/spec/prd.md) ;;
    *) return 0 ;;
  esac
  [ -f "$fp" ] || return 0

  file_root=$(dirname "$(dirname "$(dirname "$fp")")")
  canonical=$("$ARTIFACT_ROOT_RESOLVER" "$file_root" 2>/dev/null) || return 0
  canonical_prd="$canonical/spec/prd.md"
  canonical_parent=$(dirname "$canonical_prd")
  canonical_parent=$(CDPATH= cd -- "$canonical_parent" 2>/dev/null && pwd -P) || return 0
  canonical_prd="$canonical_parent/$(basename "$canonical_prd")"
  file_parent=$(dirname "$fp")
  file_parent=$(CDPATH= cd -- "$file_parent" 2>/dev/null && pwd -P) || return 0
  fp="$file_parent/$(basename "$fp")"
  [ "$fp" = "$canonical_prd" ] || return 0

  root=$(dirname "$canonical")
  key=$(printf '%s' "$root" | sed 's#[/ ]#_#g')
  mtime=$(stat -c %Y "$fp" 2>/dev/null || echo 0)

  mkdir -p "$AGENT_HOME/.spec-grounding"
  printf '%s\n' "$mtime" > "$AGENT_HOME/.spec-grounding/${sid}__${key}"
}

if [ "$#" -gt 0 ]; then
  fp=""
  sid="nosession"
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --file)
        [ "$#" -ge 2 ] || { echo "spec-read-marker: --file requires a path" >&2; exit 64; }
        fp=$2
        shift 2
        ;;
      --session)
        [ "$#" -ge 2 ] || { echo "spec-read-marker: --session requires an id" >&2; exit 64; }
        sid=$2
        shift 2
        ;;
      --agent-home)
        [ "$#" -ge 2 ] || { echo "spec-read-marker: --agent-home requires a dir" >&2; exit 64; }
        AGENT_HOME=$2
        shift 2
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        echo "spec-read-marker: unknown argument: $1" >&2
        usage >&2
        exit 64
        ;;
    esac
  done
  [ -n "$fp" ] || { echo "spec-read-marker: --file is required" >&2; exit 64; }
  mark_read "$fp" "$sid"
  exit 0
fi

input=$(cat 2>/dev/null)
[ -z "$input" ] && exit 0

fp=$(printf '%s' "$input" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"//; s/"$//')
sid=$(printf '%s' "$input" | grep -o '"session_id"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"session_id"[[:space:]]*:[[:space:]]*"//; s/"$//')
[ -z "$sid" ] && sid="nosession"

mark_read "$fp" "$sid"
exit 0
