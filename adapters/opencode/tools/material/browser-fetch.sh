#!/usr/bin/env sh
# OpenCode adapter-owned material browser-fetch launcher.
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if command -v git >/dev/null 2>&1 && ROOT=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null); then
  :
else
  ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../../.." && pwd)
fi

usage() {
  cat <<'EOF'
usage: browser-fetch.sh [--check] <url> [--out <dir>] [--timeout <ms>] [--viewport <width>x<height>] [--text-limit <chars>]

Checks or fetches a rendered web page through an OpenCode-owned material
tool-contract surface. Exit 69 means the local Playwright browser stack is
unavailable.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

printf 'adapter=opencode\n'
printf 'runtime_surface=adapter-owned-browser-fetch\n'
printf 'tool_contract=browser-fetch\n'

if [ "$#" -eq 0 ]; then
  printf 'status=tool-contract\n'
  printf 'tool_contract_check=adapters/opencode/bin/preflight.sh browser-fetch --check <url>\n'
  printf 'fallback=satisfy-tool-contract-or-report-unavailable\n'
  exit 0
fi

if [ "${AGENT_HOME:-}" ] && [ -f "$AGENT_HOME/tools/material/browser-fetch.mjs" ]; then
  :
elif [ -f "$ROOT/tools/material/browser-fetch.mjs" ]; then
  AGENT_HOME=$ROOT
else
  AGENT_HOME=$("$ROOT/adapters/opencode/utilities/agent-home.sh")
fi
export AGENT_HOME

exec node "$AGENT_HOME/tools/material/browser-fetch.mjs" "$@"
