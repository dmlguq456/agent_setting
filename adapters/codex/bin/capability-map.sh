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
compat_reference="skills/$cap/SKILL.md"
status="instruction-only"
realization="portable-instructions"
tool_contract=""
note="Codex has no native skill/plugin realization for this capability yet; read the portable catalog and task-relevant docs, then use preflight guards. Legacy compatibility references are not native input."
native_skill_path="adapters/codex/skills/$cap/SKILL.md"
native_plugin_skill_path="adapters/codex/plugins/agent-harness-codex/skills/$cap/SKILL.md"
if [ -f "$ROOT/$native_skill_path" ]; then
  native_skill=1
  realization="codex-native-skill"
  note="Codex has an adapter-owned native Skill projection generated from the portable capability spec. Use it with explicit preflight guards; legacy compatibility references are not native input."
else
  native_skill=0
  native_skill_path=""
fi
if [ -f "$ROOT/$native_plugin_skill_path" ]; then
  native_plugin=1
  [ "$native_skill" -eq 1 ] && realization="codex-native-skill-plugin"
  note="Codex has adapter-owned native Skill and plugin projections generated from the portable capability spec. Use them with explicit preflight guards; legacy compatibility references are not native input."
else
  native_plugin=0
  native_plugin_skill_path=""
fi

case "$cap" in
  autopilot-design|design-*)
    status="tool-contract"
    tool_contract="visual-harness"
    if [ "$native_plugin" -eq 1 ]; then
      note="Codex has native Skill and plugin projections for guidance and an adapter-owned visual harness contract; run the harness for concrete design outputs before claiming full support."
    elif [ "$native_skill" -eq 1 ]; then
      note="Codex has a native Skill projection for guidance and an adapter-owned visual harness contract; run the harness for concrete design outputs before claiming full support."
    else
      realization="portable-instructions"
      note="Codex has an adapter-owned visual harness contract; run the harness for concrete design outputs before claiming full support."
    fi
    ;;
esac

printf 'capability=%s\n' "$cap"
printf 'adapter=codex\n'
printf 'native_skill=%s\n' "$native_skill"
if [ -n "$native_skill_path" ]; then
  printf 'native_skill_path=%s\n' "$native_skill_path"
fi
printf 'native_plugin=%s\n' "$native_plugin"
if [ -n "$native_plugin_skill_path" ]; then
  printf 'native_plugin_skill_path=%s\n' "$native_plugin_skill_path"
fi
printf 'realization=%s\n' "$realization"
printf 'portable_source=%s\n' "$portable_source"

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
  if [ "$tool_contract" = "visual-harness" ]; then
    printf 'runtime_surface=adapter-owned-visual-harness\n'
    printf 'tool_contract_check=adapters/codex/bin/preflight.sh visual-harness <file.html>\n'
    printf 'fallback=preflight.sh visual-harness <file.html>\n'
  fi
fi
printf 'note=%s\n' "$note"
