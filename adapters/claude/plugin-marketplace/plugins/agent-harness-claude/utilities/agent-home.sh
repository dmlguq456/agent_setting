#!/usr/bin/env sh
# Print the agent harness repository directory.
# Preferred override: AGENT_HOME
# Claude adapter compatibility: CLAUDE_HOME
# Neutral default after migration: $HOME/agent_setting
# Legacy fallback: $HOME/.claude
set -eu

if [ "${AGENT_HOME:-}" ]; then
  printf '%s\n' "$AGENT_HOME"
elif [ "${CLAUDE_HOME:-}" ]; then
  printf '%s\n' "$CLAUDE_HOME"
elif [ -d "$HOME/agent_setting" ]; then
  printf '%s\n' "$HOME/agent_setting"
else
  printf '%s\n' "$HOME/.claude"
fi
