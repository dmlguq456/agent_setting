#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if command -v git >/dev/null 2>&1 && ROOT=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null); then
  :
else
  ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd)
fi

usage() {
  cat <<'EOF'
usage: distill-worker.sh <session-id> [cwd]

OpenCode transcript distillation proposal worker.

STATUS: tool-contract. The shared memory CLI has an OpenCode session source
reader based on `opencode export <session-id>`, so distill-delta works through
adapters/opencode/bin/preflight.sh.

This proposal worker must not auto-apply memory mutations until an OpenCode
no-tools worker contract is verified. Candidate: `opencode run --agent
<restricted-agent>` with deny permissions, or a future plugin-mediated worker.
Set OPENCODE_DISTILL_ENABLE=1 only when testing that contract.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

[ "$#" -ge 1 ] || { usage >&2; exit 64; }

sid=$1
cwd=${2:-$PWD}

if [ "${OPENCODE_DISTILL_ENABLE:-0}" != "1" ]; then
  cat <<EOF
adapter=opencode
status=tool-contract
tool_contract=no-tools-distill-worker
runtime_surface=unverified
reason=no-tools-worker-unverified
delta_surface=adapters/opencode/bin/preflight.sh distill-delta <session-id>
fallback=inspect-distill-delta-or-enable-after-contract-review
cwd=$cwd
session_id=$sid
EOF
  exit 69
fi

cat <<EOF
adapter=opencode
status=tool-contract
tool_contract=no-tools-distill-worker
runtime_surface=unverified
reason=no-tools-worker-unverified
delta_surface=adapters/opencode/bin/preflight.sh distill-delta <session-id>
fallback=inspect-distill-delta-or-enable-after-contract-review
cwd=$cwd
session_id=$sid
EOF
exit 69
