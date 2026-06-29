#!/usr/bin/env bash
# Claude /track adapter wrapper. The toggle semantics live in workflow-toggle.sh.
set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec bash "$SCRIPT_DIR/utilities/workflow-toggle.sh" --cwd "$PWD" --session "${CLAUDE_CODE_SESSION_ID:-}"
