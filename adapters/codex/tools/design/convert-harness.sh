#!/usr/bin/env sh
# Codex adapter-owned design converter wrapper (PDF/PPTX/bundle export).
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if command -v git >/dev/null 2>&1 && ROOT=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null); then
  :
else
  ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../../.." && pwd)
fi

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ] || [ "$#" -eq 0 ]; then
  cat <<'EOF'
usage: convert-harness.sh <pdf|bundle|pptx> <input.html> [output] [--selector .slide]

Exports a design HTML artifact to PDF (1 slide = 1 page), a single-file offline
bundle (local assets inlined), or PPTX (per-slide PNG + speaker notes). Codex
adapter-owned wrapper around the shared design converter. bundle is pure Node;
pdf/pptx require Playwright (and pptxgenjs for pptx) and exit non-zero when those
deps are unavailable.
EOF
  exit 0
fi

if [ "${AGENT_HOME:-}" ] && [ -f "$AGENT_HOME/tools/design-mcp/convert.mjs" ]; then
  :
elif [ -f "$ROOT/tools/design-mcp/convert.mjs" ]; then
  AGENT_HOME=$ROOT
else
  AGENT_HOME=$("$ROOT/adapters/codex/utilities/agent-home.sh")
fi
export AGENT_HOME

if [ ! -f "$AGENT_HOME/tools/design-mcp/convert.mjs" ]; then
  printf 'adapter=codex\nstatus=tool-contract\nruntime_surface=adapter-owned-design-convert\nreason=design-converter-unavailable\n' >&2
  exit 69
fi

printf 'adapter=codex\n'
printf 'runtime_surface=adapter-owned-design-convert\n'
exec node "$AGENT_HOME/tools/design-mcp/convert.mjs" "$@"
