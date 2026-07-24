#!/bin/sh
# capability-grounding.sh — record the acting session's inline entry capability so Fleet can
# show `capability(mode·intensity)` for work that never dispatches (and thus leaves no jobs.log
# row). Sibling of the spec-read grounding marker: dispatched work is grounded by jobs.log/route,
# inline work by this marker. POSIX sh, no jq.
#
#   capability-grounding.sh record --sid <id> --capability <name> \
#       [--mode <m>] [--intensity <i>] [--agent-home <dir>] [--cwd <dir>]
#
# Writes `<agent-home>/.capability-grounding/<sid>` with KV lines. Overwrites on each call, so the
# freshest entry-skill invocation wins (the session's CURRENT capability). Fleet reads the file's
# mtime for freshness (same sid-reuse rule as the spec marker) and the KV body for the tag.

set -eu

AGENT_HOME="${AGENT_HOME:-${CLAUDE_HOME:-}}"

# The fixed, capability-agnostic intensity vocabulary (CONVENTIONS §1.1). A mode is
# capability-specific, so the caller passes it explicitly; only the value is validated as
# non-empty. An unrecognized intensity is dropped rather than stored (honest omission).
valid_intensity() {
  case "$1" in
    direct|quick|standard|strong|thorough|adversarial) return 0 ;;
    *) return 1 ;;
  esac
}

record() {
  sid="" cap="" mode="" intensity="" cwd=""
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --sid) sid=${2:-}; shift 2 ;;
      --capability) cap=${2:-}; shift 2 ;;
      --mode) mode=${2:-}; shift 2 ;;
      --intensity) intensity=${2:-}; shift 2 ;;
      --cwd) cwd=${2:-}; shift 2 ;;
      --agent-home) AGENT_HOME=${2:-}; shift 2 ;;
      *) echo "capability-grounding: unknown argument: $1" >&2; return 64 ;;
    esac
  done
  [ -n "$sid" ] || { echo "capability-grounding: --sid is required" >&2; return 64; }
  [ -n "$cap" ] || { echo "capability-grounding: --capability is required" >&2; return 64; }
  [ -n "$AGENT_HOME" ] || return 0
  # Only the entry-capability set is grounded; a sub-skill or tool call is not a session identity.
  case "$cap" in
    autopilot-apply|autopilot-code|autopilot-design|autopilot-draft|autopilot-lab|autopilot-note|autopilot-refine|autopilot-research|autopilot-ship|autopilot-spec) ;;
    *) return 0 ;;
  esac
  valid_intensity "$intensity" || intensity=""

  dir="$AGENT_HOME/.capability-grounding"
  mkdir -p "$dir" 2>/dev/null || return 0
  tmp="$dir/.$sid.tmp.$$"
  {
    printf 'capability=%s\n' "$cap"
    [ -n "$mode" ] && printf 'mode=%s\n' "$mode"
    [ -n "$intensity" ] && printf 'intensity=%s\n' "$intensity"
    [ -n "$cwd" ] && printf 'cwd=%s\n' "$cwd"
    :   # keep the block's exit status 0 even when the last optional field is empty
  } > "$tmp" 2>/dev/null || { rm -f "$tmp" 2>/dev/null; return 0; }
  mv -f "$tmp" "$dir/$sid" 2>/dev/null || rm -f "$tmp" 2>/dev/null
}

case "${1:-}" in
  record) shift; record "$@" ;;
  -h|--help|"") echo "usage: capability-grounding.sh record --sid <id> --capability <name> [--mode <m>] [--intensity <i>] [--agent-home <dir>] [--cwd <dir>]" ;;
  *) echo "capability-grounding: unknown command: $1" >&2; exit 64 ;;
esac
