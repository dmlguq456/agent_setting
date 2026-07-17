#!/usr/bin/env sh
# Codex adapter launcher for the shared memory CLI.
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if command -v git >/dev/null 2>&1 && ROOT=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null); then
  :
else
  ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../../.." && pwd)
fi

if [ -n "${AGENT_HOME:-}" ] && [ -f "$AGENT_HOME/tools/memory/mem.py" ]; then
  :
elif [ -f "$ROOT/tools/memory/mem.py" ]; then
  AGENT_HOME=$ROOT
else
  AGENT_HOME=$("$ROOT/adapters/codex/utilities/agent-home.sh")
fi
export AGENT_HOME

if [ ! -f "$AGENT_HOME/tools/memory/mem.py" ]; then
  echo "codex memory launcher: AGENT_HOME does not point to an agent harness: $AGENT_HOME" >&2
  exit 69
fi

exec python3 "$AGENT_HOME/tools/memory/mem.py" "$@"
