#!/usr/bin/env sh
# Print the active agent harness root (managed release or linked checkout).
# Preferred override: AGENT_HOME
# Claude adapter compatibility: CLAUDE_HOME
# Managed-release default: $XDG_DATA_HOME/agent-harness/current
# Linked-checkout fallback: $HOME/agent_setting
# Legacy fallback: $HOME/.claude
set -eu

# Windows/Git Bash: a child process's $HOME is reset to the MSYS home
# (e.g. C:\msys64\home\<user>) and $USERPROFILE is dropped, so trusting either
# misplaces the memory store — the linked checkout lives under the Windows user
# profile. Derive the profile via cygpath (env-independent); the mixed
# C:/Users/<user> form is stat-able by MSYS `test -d` and read correctly by a
# native python (mem.py). Empty on non-Windows (no cygpath) → POSIX $HOME is used.
up=""
if command -v cygpath >/dev/null 2>&1; then
  _pf="$(cygpath -H 2>/dev/null)/$(basename "$HOME")"
  up="$(cygpath -m "$_pf" 2>/dev/null || printf '%s' "$_pf")"
fi

if [ "${AGENT_HOME:-}" ]; then
  printf '%s\n' "$AGENT_HOME"
elif [ "${CLAUDE_HOME:-}" ]; then
  printf '%s\n' "$CLAUDE_HOME"
elif [ -d "${XDG_DATA_HOME:-$HOME/.local/share}/agent-harness/current" ]; then
  printf '%s\n' "${XDG_DATA_HOME:-$HOME/.local/share}/agent-harness/current"
elif [ -n "$up" ] && [ -d "$up/agent_setting" ]; then
  printf '%s\n' "$up/agent_setting"
elif [ -d "$HOME/agent_setting" ]; then
  printf '%s\n' "$HOME/agent_setting"
elif [ -n "$up" ] && [ -d "$up/.claude" ]; then
  printf '%s\n' "$up/.claude"
else
  printf '%s\n' "$HOME/.claude"
fi
