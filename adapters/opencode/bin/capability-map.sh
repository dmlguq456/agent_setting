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

Prints how the OpenCode adapter realizes a portable capability.
EOF
}

[ "${1:-}" != "-h" ] && [ "${1:-}" != "--help" ] || { usage; exit 0; }
[ "$#" -eq 1 ] || { usage >&2; exit 64; }

cap=$1

if [ ! -f "$CATALOG" ]; then
  echo "opencode capability-map: missing capabilities catalog" >&2
  exit 69
fi

if ! grep -Fq "| \`$cap\` |" "$CATALOG"; then
  echo "opencode capability-map: unknown capability: $cap" >&2
  exit 64
fi

if [ -f "$ROOT/capabilities/$cap.md" ]; then
  portable_source="capabilities/$cap.md"
else
  portable_source="capabilities/README.md"
fi
compat_reference="skills/$cap/SKILL.md"
native_skill_path="adapters/opencode/skills/$cap/SKILL.md"
native_command_path="adapters/opencode/commands/$cap.md"
status="instruction-only"
realization="opencode-native-skill-command"
tool_contract=""
note="OpenCode has adapter-owned native Skill and command projections generated from the portable capability spec. Use them with explicit preflight guards; legacy compatibility references are not native input."

case "$cap" in
  autopilot-design|design-*)
    status="tool-contract"
    realization="opencode-native-skill-command"
    tool_contract="visual-harness"
    note="OpenCode has native Skill and command projections for guidance, but must provide an adapter visual harness equivalent before claiming full design capability support; legacy visual harness files are reference only."
    ;;
esac

printf 'capability=%s\n' "$cap"
printf 'adapter=opencode\n'
if [ -f "$ROOT/$native_skill_path" ]; then
  printf 'native_skill=1\n'
  printf 'native_skill_path=%s\n' "$native_skill_path"
else
  printf 'native_skill=0\n'
  printf 'native_skill_path=\n'
  realization="portable-instructions"
fi
if [ -f "$ROOT/$native_command_path" ]; then
  printf 'native_command=1\n'
  printf 'native_command_path=%s\n' "$native_command_path"
elif [ "$realization" = "opencode-native-skill-command" ]; then
  printf 'native_command=0\n'
  printf 'native_command_path=\n'
  realization="opencode-native-skill"
else
  printf 'native_command=0\n'
  printf 'native_command_path=\n'
fi
printf 'realization=%s\n' "$realization"
printf 'portable_source=%s\n' "$portable_source"

if [ -f "$ROOT/$compat_reference" ]; then
  printf 'compat_reference=%s\n' "$compat_reference"
else
  printf 'compat_reference=\n'
fi

printf 'bootstrap=adapters/opencode/AGENTS.md\n'
printf 'guards=adapters/opencode/bin/preflight.sh\n'
printf 'status=%s\n' "$status"
if [ -n "$tool_contract" ]; then
  printf 'tool_contract=%s\n' "$tool_contract"
  if [ "$tool_contract" = "visual-harness" ]; then
    printf 'tool_contract_check=adapters/opencode/bin/preflight.sh visual-harness\n'
    printf 'runtime_surface=not-materialized\n'
    printf 'fallback=preflight.sh design <file>\n'
  fi
fi
printf 'note=%s\n' "$note"
