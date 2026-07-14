#!/bin/sh
# Clone-free Agent Harness bootstrap. The downloaded distribution module
# verifies the release archive checksum before publishing or activating it.
set -eu

PY=$(command -v python3 || command -v python || true)
if [ -z "$PY" ]; then
  echo "agent-harness: Python 3.10+ is required." >&2
  exit 1
fi

REPOSITORY=${HARNESS_REPOSITORY:-dmlguq456/agent_setting}
BOOTSTRAP_REF=${HARNESS_BOOTSTRAP_REF:-main}
BOOTSTRAP_URL=${HARNESS_BOOTSTRAP_URL:-https://raw.githubusercontent.com/$REPOSITORY/$BOOTSTRAP_REF/tools/install/distribution.py}
TMP=$(mktemp -d "${TMPDIR:-/tmp}/agent-harness-bootstrap.XXXXXX")
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
MODULE="$TMP/distribution.py"

if command -v curl >/dev/null 2>&1; then
  curl -fsSL --proto '=https' --tlsv1.2 "$BOOTSTRAP_URL" -o "$MODULE"
elif command -v wget >/dev/null 2>&1; then
  case "$BOOTSTRAP_URL" in
    https://*) ;;
    *) echo "agent-harness: bootstrap URL must use HTTPS." >&2; exit 1 ;;
  esac
  wget -qO "$MODULE" "$BOOTSTRAP_URL"
else
  echo "agent-harness: curl or wget is required." >&2
  exit 1
fi

"$PY" "$MODULE" bootstrap --repository "$REPOSITORY" "$@"
