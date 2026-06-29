#!/usr/bin/env sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
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
claude_reference="skills/$cap/SKILL.md"

printf 'capability=%s\n' "$cap"
printf 'adapter=codex\n'
printf 'native_skill=0\n'
printf 'realization=portable-instructions\n'
printf 'portable_source=%s\n' "$portable_source"

if [ -f "$ROOT/$claude_reference" ]; then
  printf 'compat_reference=%s\n' "$claude_reference"
else
  printf 'compat_reference=\n'
fi

printf 'bootstrap=adapters/codex/AGENTS.md\n'
printf 'guards=adapters/codex/bin/preflight.sh\n'
printf 'status=available-manual\n'
printf 'note=Codex must read the portable catalog and task-relevant docs; Claude Skill frontmatter is reference only.\n'
