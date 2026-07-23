#!/bin/sh
# Claude adapter payload wrapper for the portable supervised-parent guard.
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ -z "$AGENT_HOME" ]; then
  AGENT_HOME=$("$SCRIPT_DIR/../utilities/agent-home.sh")
fi
exec "$AGENT_HOME/hooks/registered-parent-park.py" "$@"
