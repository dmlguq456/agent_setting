#!/usr/bin/env bash
# Deprecated compatibility shim for stale runtime projections.
#
# Semantic recall is agent-initiated. Current adapters do not register this
# script as a prompt hook, and the shim never classifies prompts, reads the
# memory store, or emits context. Keeping a fail-open executable avoids breaking
# an installed projection that has not yet been refreshed.
set -u

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  cat <<'EOF'
mem-recall-inject.sh is deprecated.
Memory retrieval is agent-initiated through tools/memory/recall.sh or mem recall.
This compatibility shim always exits successfully without emitting context.
EOF
  exit 0
fi

# Drain hook payloads so an upstream writer does not see SIGPIPE.
if [ "$#" -eq 0 ]; then
  cat >/dev/null 2>&1 || true
fi

exit 0
