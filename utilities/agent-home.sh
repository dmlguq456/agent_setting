#!/usr/bin/env sh
# Print the agent harness home directory.
# Preferred override: AGENT_HOME
# Claude adapter compatibility: CLAUDE_HOME
# Default install path: $HOME/.claude
set -eu

printf '%s\n' "${AGENT_HOME:-${CLAUDE_HOME:-$HOME/.claude}}"
