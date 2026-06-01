#!/usr/bin/env bash
# PostToolUse hook (Edit|Write|MultiEdit) — spec component ⑥.
# Auto-renders a saved DESIGN HTML file headlessly and alerts the agent if the console errors.
# Fast no-op for non-design / non-HTML edits (the node checker self-filters from the hook JSON).
# Opt out per shell with DESIGN_POSTWRITE_HOOK=0.
[ "${DESIGN_POSTWRITE_HOOK:-1}" = "0" ] && exit 0
exec node "$HOME/.claude/tools/design-mcp/console-check.mjs" --hook
