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
native_skill_path="adapters/opencode/skills/$cap/SKILL.md"
native_command_path="adapters/opencode/commands/$cap.md"
status="instruction-only"
realization="portable-instructions"
tool_contract=""
note="OpenCode has no native Skill/command realization for this capability yet; read the portable catalog and task-relevant docs, then use preflight guards. Legacy compatibility references are not native input."

case "$cap" in
  autopilot-design|design-*)
    status="tool-contract"
    tool_contract="visual-harness"
    ;;
esac

printf 'capability=%s\n' "$cap"
printf 'adapter=opencode\n'
if [ -f "$ROOT/$native_skill_path" ]; then
  native_skill=1
  printf 'native_skill=1\n'
  printf 'native_skill_path=%s\n' "$native_skill_path"
  realization="opencode-native-skill"
  note="OpenCode has an adapter-owned native Skill projection generated from the portable capability spec. Use it with explicit preflight guards; legacy compatibility references are not native input."
else
  native_skill=0
  printf 'native_skill=0\n'
  printf 'native_skill_path=\n'
fi
if [ -f "$ROOT/$native_command_path" ]; then
  native_command=1
  printf 'native_command=1\n'
  printf 'native_command_path=%s\n' "$native_command_path"
  if [ "$native_skill" -eq 1 ]; then
    realization="opencode-native-skill-command"
    note="OpenCode has adapter-owned native Skill and command projections generated from the portable capability spec. Use them with explicit preflight guards; legacy compatibility references are not native input."
  else
    realization="opencode-native-command"
    note="OpenCode has an adapter-owned native command projection generated from the portable capability spec. Use it with explicit preflight guards; legacy compatibility references are not native input."
  fi
else
  native_command=0
  printf 'native_command=0\n'
  printf 'native_command_path=\n'
fi
if [ "$tool_contract" = "visual-harness" ]; then
  case "$realization" in
    opencode-native-skill-command)
      note="OpenCode has native Skill and command projections for guidance and an adapter-owned visual harness contract; run the harness for concrete design outputs before claiming full support."
      ;;
    opencode-native-skill)
      note="OpenCode has a native Skill projection for guidance and an adapter-owned visual harness contract; run the harness for concrete design outputs before claiming full support."
      ;;
    opencode-native-command)
      note="OpenCode has a native command projection for guidance and an adapter-owned visual harness contract; run the harness for concrete design outputs before claiming full support."
      ;;
    *)
      note="OpenCode has an adapter-owned visual harness contract; run the harness for concrete design outputs before claiming full support."
      ;;
  esac
fi
printf 'realization=%s\n' "$realization"
printf 'portable_source=%s\n' "$portable_source"
printf 'compat_reference=not-projected\n'

printf 'bootstrap=adapters/opencode/AGENTS.md\n'
printf 'guards=adapters/opencode/bin/preflight.sh\n'
printf 'status=%s\n' "$status"
if [ -n "$tool_contract" ]; then
  printf 'tool_contract=%s\n' "$tool_contract"
  if [ "$tool_contract" = "visual-harness" ]; then
    printf 'runtime_surface=adapter-owned-visual-harness\n'
    printf 'tool_contract_check=adapters/opencode/bin/preflight.sh visual-harness <file.html>\n'
    printf 'fallback=preflight.sh visual-harness <file.html>\n'
  fi
fi
printf 'note=%s\n' "$note"
