#!/usr/bin/env sh
# Codex adapter-owned visual harness wrapper.
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if command -v git >/dev/null 2>&1 && ROOT=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null); then
  :
else
  ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../../.." && pwd)
fi

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  cat <<'EOF'
usage: visual-harness.sh <file.html> [--out <dir>] [--viewport <width>x<height>]

Renders an HTML design artifact, captures a screenshot, and reports console
errors. This is a Codex adapter-owned wrapper around the shared design checker.
EOF
  exit 0
fi

if [ "${AGENT_HOME:-}" ] && [ -f "$AGENT_HOME/tools/design-mcp/visual-check.mjs" ]; then
  :
elif [ -f "$ROOT/tools/design-mcp/visual-check.mjs" ]; then
  AGENT_HOME=$ROOT
else
  AGENT_HOME=$("$ROOT/adapters/codex/utilities/agent-home.sh")
fi
export AGENT_HOME

printf 'adapter=codex\n'
printf 'runtime_surface=adapter-owned-visual-harness\n'
exec node "$AGENT_HOME/tools/design-mcp/visual-check.mjs" "$@"
