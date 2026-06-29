#!/usr/bin/env bash
# PostToolUse hook (Edit|Write|MultiEdit) — spec component ⑥.
# Auto-renders a saved DESIGN HTML file headlessly and alerts the agent if the console errors.
# Fast no-op for non-design / non-HTML edits (the node checker self-filters from the hook JSON).
# Portable CLI: design-postwrite.sh --file <path>
# Opt out per shell with DESIGN_POSTWRITE_HOOK=0.
AGENT_HOME="${AGENT_HOME:-${CLAUDE_HOME:-$HOME/.claude}}"
[ "${DESIGN_POSTWRITE_HOOK:-1}" = "0" ] && exit 0

if [ "${1:-}" = "--file" ]; then
  [ "$#" -ge 2 ] || { echo "design-postwrite: --file requires a path" >&2; exit 64; }
  exec node "$AGENT_HOME/tools/design-mcp/console-check.mjs" "$2"
fi
if [ "$#" -gt 0 ]; then
  case "$1" in
    -h|--help)
      cat <<'EOF'
usage: design-postwrite.sh --file <path>

Without arguments, reads Claude PostToolUse hook JSON from stdin.
EOF
      exit 0
      ;;
    *)
      echo "design-postwrite: unknown argument: $1" >&2
      exit 64
      ;;
  esac
fi

exec node "$AGENT_HOME/tools/design-mcp/console-check.mjs" --hook
