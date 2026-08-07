#!/usr/bin/env sh
# Print the agent harness repository directory for the Codex adapter.
# Preferred override: valid AGENT_HOME
# Neutral default after migration: $HOME/agent_setting
# Optional Codex runtime pointer: $HOME/.codex/hearting
set -eu

if [ -n "${AGENT_HOME:-}" ] && [ -f "$AGENT_HOME/core/CORE.md" ]; then
  printf '%s\n' "$AGENT_HOME"
elif [ -f "$HOME/agent_setting/core/CORE.md" ]; then
  printf '%s\n' "$HOME/agent_setting"
elif [ -f "$HOME/.codex/hearting/core/CORE.md" ]; then
  printf '%s\n' "$HOME/.codex/hearting"
else
  printf '%s\n' "$HOME/agent_setting"
fi
