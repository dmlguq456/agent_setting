#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if command -v git >/dev/null 2>&1 && ROOT=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null); then
  :
else
  ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd)
fi
CATALOG="$ROOT/capabilities/README.md"

usage() {
  cat <<'EOF'
usage: capability-map.sh <capability>

Prints how the Codex adapter realizes a portable capability.
EOF
}

[ "${1:-}" != "-h" ] && [ "${1:-}" != "--help" ] || { usage; exit 0; }
[ "$#" -eq 1 ] || { usage >&2; exit 64; }

cap=$1

if [ ! -f "$CATALOG" ]; then
  echo "codex capability-map: missing capabilities catalog" >&2
  exit 69
fi

if ! grep -Fq "| \`$cap\` |" "$CATALOG"; then
  echo "codex capability-map: unknown capability: $cap" >&2
  exit 64
fi

if [ -f "$ROOT/capabilities/$cap.md" ]; then
  portable_source="capabilities/$cap.md"
else
  portable_source="capabilities/README.md"
fi
claude_realization="adapters/claude/skills/$cap/SKILL.md"
compat_reference="skills/$cap/SKILL.md"
status="instruction-only"
realization="portable-instructions"
tool_contract=""
note="Codex has no native skill/plugin realization for this capability yet; read the portable catalog and task-relevant docs, then use preflight guards. Claude Skill frontmatter is reference only."

case "$cap" in
  autopilot-design|design-*)
    status="tool-contract"
    realization="portable-instructions"
    tool_contract="visual-harness"
    note="Codex must provide an adapter visual harness equivalent before claiming full design capability support; Claude Design MCP files are reference only."
    ;;
esac

printf 'capability=%s\n' "$cap"
printf 'adapter=codex\n'
printf 'native_skill=0\n'
printf 'realization=%s\n' "$realization"
printf 'portable_source=%s\n' "$portable_source"

if [ -f "$ROOT/$claude_realization" ]; then
  printf 'claude_realization=%s\n' "$claude_realization"
else
  printf 'claude_realization=\n'
fi

if [ -f "$ROOT/$compat_reference" ]; then
  printf 'compat_reference=%s\n' "$compat_reference"
else
  printf 'compat_reference=\n'
fi

printf 'bootstrap=adapters/codex/AGENTS.md\n'
printf 'guards=adapters/codex/bin/preflight.sh\n'
printf 'status=%s\n' "$status"
if [ -n "$tool_contract" ]; then
  printf 'tool_contract=%s\n' "$tool_contract"
fi
printf 'note=%s\n' "$note"
