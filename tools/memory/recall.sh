#!/usr/bin/env bash
# recall — unified-memory retrieval (thin wrapper around mem recall).
#   Searches the unified store (durable + working), profile-tier records, and
#   raw conversations with --sessions rather than scanning legacy files.
#   Usage: recall.sh "<query>" [--tier working|durable] [--scope project|global]
#         [--all] [--sessions] [--full] [--limit 1..100]
#   Retrieval does not consume handoffs. Explicit recall updates only
#   last_accessed; --no-touch leaves access metadata unchanged.
#   Details: tools/memory/README.md and MEMORY §7.4.
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
AGENT_HOME="${AGENT_HOME:-$("$SCRIPT_DIR/../../utilities/agent-home.sh")}"
export AGENT_HOME
# Interpreter discovery. On Windows the `python3`/`python` on PATH are WindowsApps
# app-execution aliases (a pymanager stub that hangs for minutes trying to reinstall
# Python), so prefer the `py` launcher (a real installer-based python). MEM_PYTHON
# overrides discovery (mirrors FLEET_PYTHON in tools/fleet/fleet.sh).
if [ -n "${MEM_PYTHON:-}" ]; then
  PY="$MEM_PYTHON"
elif command -v py >/dev/null 2>&1 && py -3 -c "" >/dev/null 2>&1; then
  PY="py -3"
else
  PY=$(command -v python3 || command -v python || true)
fi
[ -n "$PY" ] || { echo "recall: no usable python interpreter found" >&2; exit 1; }
# mem.py is a sibling of this script; use SCRIPT_DIR (not $AGENT_HOME/tools/...) so
# a split layout — code in .claude, data root in $AGENT_HOME (agent_setting) — works.
# AGENT_HOME is still exported above so mem.py locates the store/DB.
exec $PY "$SCRIPT_DIR/mem.py" recall "$@"
