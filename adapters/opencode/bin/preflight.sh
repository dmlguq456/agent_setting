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
usage: preflight.sh write <file> [session-id]
       preflight.sh read <file> [session-id]
       preflight.sh capability <name> [cwd] [session-id]
       preflight.sh skill <name> [cwd] [session-id]
       preflight.sh start [cwd] [session-id]
       preflight.sh mode [cwd] [session-id]
       preflight.sh track [cwd] [session-id]
       preflight.sh memory [cwd]
       preflight.sh recall <prompt> [cwd]
       preflight.sh briefing [cwd]
       preflight.sh worklog [cwd]
       preflight.sh design <file>
       preflight.sh visual-harness [file.html]
       preflight.sh distill-delta <session-id>
       preflight.sh distill-propose <session-id> [cwd]
       preflight.sh role <portable-role>
       preflight.sh capability-info <capability>
       preflight.sh mode-info <family/mode>

Runs portable checks that OpenCode can call without consuming Claude hook JSON,
settings.json, or statusline.sh. The adapter also provides an OpenCode JS
plugin guard for write/edit/patch tools; use these wrappers as explicit
preflight checks when that plugin is not installed or trusted.
EOF
}

cmd=${1:-}
case "$cmd" in
  write)
    [ "$#" -ge 2 ] || { echo "opencode preflight: write requires a file path" >&2; exit 64; }
    file=$2
    sid=${3:-opencode}
    "$ROOT/hooks/git-state-guard.sh" --file "$file"
    ARTIFACT_GUARD_TOGGLE_LABEL="preflight.sh track" "$ROOT/hooks/artifact-guard.sh" --file "$file" --session "$sid"
    "$ROOT/hooks/builtin-memory-guard.sh" --file "$file"
    ;;
  read)
    [ "$#" -ge 2 ] || { echo "opencode preflight: read requires a file path" >&2; exit 64; }
    file=$2
    sid=${3:-opencode}
    "$ROOT/hooks/spec-read-marker.sh" --file "$file" --session "$sid"
    ;;
  capability|skill)
    [ "$#" -ge 2 ] || { echo "opencode preflight: $cmd requires a capability name" >&2; exit 64; }
    name=$2
    cwd=${3:-$PWD}
    sid=${4:-opencode}
    "$ROOT/hooks/spec-skill-gate.sh" --skill "$name" --cwd "$cwd" --session "$sid"
    ;;
  start)
    cwd=${2:-$PWD}
    sid=${3:-opencode}
    "$ROOT/utilities/workflow-guard-hook.sh" --event start --cwd "$cwd" --session "$sid" --format text
    ;;
  mode)
    cwd=${2:-$PWD}
    sid=${3:-opencode}
    "$ROOT/utilities/workflow-guard-hook.sh" --event prompt --cwd "$cwd" --session "$sid" --format text --toggle-label "preflight.sh track"
    ;;
  track)
    cwd=${2:-$PWD}
    sid=${3:-opencode}
    "$ROOT/utilities/workflow-toggle.sh" --cwd "$cwd" --session "$sid"
    ;;
  memory)
    cwd=${2:-$PWD}
    (cd "$cwd" && AGENT_HOME="${AGENT_HOME:-$ROOT}" python3 "$ROOT/tools/memory/mem.py" inject)
    ;;
  recall)
    [ "$#" -ge 2 ] || { echo "opencode preflight: recall requires prompt text" >&2; exit 64; }
    prompt=$2
    cwd=${3:-$PWD}
    AGENT_HOME="${AGENT_HOME:-$ROOT}" "$ROOT/hooks/mem-recall-inject.sh" --prompt "$prompt" --cwd "$cwd" --format text
    ;;
  briefing)
    cwd=${2:-$PWD}
    AGENT_HOME="${AGENT_HOME:-$ROOT}" bash "$ROOT/hooks/mem-briefing-inject.sh" --cwd "$cwd" --format text
    ;;
  worklog)
    cwd=${2:-$PWD}
    AGENT_HOME="${AGENT_HOME:-$ROOT}" \
      AGENT_NOTES_ROOT="${AGENT_NOTES_ROOT:-${WORKLOG_NOTES_ROOT:-}}" \
      WORKLOG_BOARD_APP="${WORKLOG_BOARD_APP:-}" \
      WORKLOG_BOARD_WT="${WORKLOG_BOARD_WT:-}" \
      "$ROOT/utilities/agent-worklog-state.sh" "$cwd"
    ;;
  design)
    [ "$#" -ge 2 ] || { echo "opencode preflight: design requires a file path" >&2; exit 64; }
    file=$2
    AGENT_HOME="$ROOT" bash "$ROOT/hooks/design-postwrite.sh" --file "$file"
    ;;
  visual-harness)
    if [ "$#" -ge 2 ]; then
      shift
      "$ROOT/adapters/opencode/tools/design/visual-harness.sh" "$@"
      exit $?
    fi
    cat <<'EOF'
adapter=opencode
status=tool-contract
tool_contract=visual-harness
runtime_surface=adapter-owned-visual-harness
tool_contract_check=adapters/opencode/bin/preflight.sh visual-harness <file.html>
fallback=preflight.sh visual-harness <file.html>
portable_source=capabilities/autopilot-design.md
note=OpenCode design capabilities have native Skill/Command guidance and an adapter-owned render/screenshot/console harness. Run it for every design HTML output, then inspect the screenshot before claiming visual completion.
EOF
    ;;
  distill-delta)
    [ "$#" -ge 2 ] || { echo "opencode preflight: distill-delta requires a session id" >&2; exit 64; }
    sid=$2
    AGENT_HOME="${AGENT_HOME:-$ROOT}" python3 "$ROOT/tools/memory/mem.py" distill "$sid" --source opencode
    ;;
  distill-propose)
    [ "$#" -ge 2 ] || { echo "opencode preflight: distill-propose requires a session id" >&2; exit 64; }
    sid=$2
    cwd=${3:-$PWD}
    "$ROOT/adapters/opencode/bin/distill-worker.sh" "$sid" "$cwd"
    ;;
  role)
    [ "$#" -ge 2 ] || { echo "opencode preflight: role requires a portable role" >&2; exit 64; }
    shift
    "$ROOT/adapters/opencode/bin/role-map.sh" "$@"
    ;;
  capability-info)
    [ "$#" -eq 2 ] || { echo "opencode preflight: capability-info requires one capability" >&2; exit 64; }
    "$ROOT/adapters/opencode/bin/capability-map.sh" "$2"
    ;;
  mode-info)
    [ "$#" -eq 2 ] || { echo "opencode preflight: mode-info requires one family/mode" >&2; exit 64; }
    "$ROOT/adapters/opencode/bin/mode-map.sh" "$2"
    ;;
  -h|--help|"")
    usage
    exit 0
    ;;
  *)
    echo "opencode preflight: unknown command: $cmd" >&2
    usage >&2
    exit 64
    ;;
esac
