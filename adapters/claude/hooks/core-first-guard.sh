#!/bin/sh
# PreToolUse(Edit/Write): require a current-session core/*.md read marker before
# editing adapters/**.
# S6 (2026-07-09): use a wrapper instead of a full copy. The paired read-marker
# wrapper writes under the repository `.core-grounding`; a copied guard resolved
# SCRIPT_DIR/.. to ~/.claude and always denied because it inspected a different
# marker directory. Executing the repository-owned portable guard keeps both
# sides on the same AGENT_HOME while preserving stdin-JSON and --file modes.
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
AGENT_HOME="${AGENT_HOME:-$("$SCRIPT_DIR/../utilities/agent-home.sh")}"
exec "$AGENT_HOME/hooks/core-first-guard.sh" "$@"
