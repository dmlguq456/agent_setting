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
       preflight.sh status [cwd] [session-id]
       preflight.sh worklog [cwd]
       preflight.sh claim-verify [--check] <claim> [--out <file>]
       preflight.sh browser-fetch [--check] <url> [--out <dir>]
       preflight.sh data-script [--check] <script.py> [-- args...]
       preflight.sh figure-gen [--check] <script.py> [-- args...]
       preflight.sh pdf-extract [--check] <file.pdf> [--out <file.txt>]
       preflight.sh web-image-search [--check] <query> [--max-results N] [--out <file>]
       preflight.sh verification-runner [--check] [--timeout seconds] -- <command> [args...]
       preflight.sh design <file>
       preflight.sh visual-harness [file.html]
       preflight.sh distill-delta <session-id>
       preflight.sh distill-propose <session-id> [cwd]
       preflight.sh role <portable-role>
       preflight.sh capability-info <capability>
       preflight.sh mode-info <family/mode>

Runs portable checks that Codex can call without consuming Claude hook JSON or
settings.json.
EOF
}

cmd=${1:-}
case "$cmd" in
  write)
    [ "$#" -ge 2 ] || { echo "codex preflight: write requires a file path" >&2; exit 64; }
    file=$2
    sid=${3:-codex}
    "$ROOT/hooks/git-state-guard.sh" --file "$file"
    ARTIFACT_GUARD_TOGGLE_LABEL="preflight.sh track" "$ROOT/hooks/artifact-guard.sh" --file "$file" --session "$sid"
    "$ROOT/hooks/builtin-memory-guard.sh" --file "$file"
    ;;
  read)
    [ "$#" -ge 2 ] || { echo "codex preflight: read requires a file path" >&2; exit 64; }
    file=$2
    sid=${3:-codex}
    "$ROOT/hooks/spec-read-marker.sh" --file "$file" --session "$sid"
    ;;
  capability|skill)
    [ "$#" -ge 2 ] || { echo "codex preflight: $cmd requires a capability name" >&2; exit 64; }
    name=$2
    cwd=${3:-$PWD}
    sid=${4:-codex}
    "$ROOT/hooks/spec-skill-gate.sh" --skill "$name" --cwd "$cwd" --session "$sid"
    ;;
  start)
    cwd=${2:-$PWD}
    sid=${3:-codex}
    "$ROOT/utilities/workflow-guard-hook.sh" --event start --cwd "$cwd" --session "$sid" --format text
    ;;
  mode)
    cwd=${2:-$PWD}
    sid=${3:-codex}
    "$ROOT/utilities/workflow-guard-hook.sh" --event prompt --cwd "$cwd" --session "$sid" --format text --toggle-label "preflight.sh track"
    ;;
  track)
    cwd=${2:-$PWD}
    sid=${3:-codex}
    "$ROOT/utilities/workflow-toggle.sh" --cwd "$cwd" --session "$sid"
    ;;
  memory)
    cwd=${2:-$PWD}
    (cd "$cwd" && AGENT_HOME="${AGENT_HOME:-$ROOT}" python3 "$ROOT/tools/memory/mem.py" inject)
    ;;
  recall)
    [ "$#" -ge 2 ] || { echo "codex preflight: recall requires prompt text" >&2; exit 64; }
    prompt=$2
    cwd=${3:-$PWD}
    AGENT_HOME="${AGENT_HOME:-$ROOT}" "$ROOT/hooks/mem-recall-inject.sh" --prompt "$prompt" --cwd "$cwd" --format text
    ;;
  briefing)
    cwd=${2:-$PWD}
    AGENT_HOME="${AGENT_HOME:-$ROOT}" bash "$ROOT/hooks/mem-briefing-inject.sh" --cwd "$cwd" --format text
    ;;
  status)
    cwd=${2:-$PWD}
    sid=${3:-codex}
    AGENT_ADAPTER=codex "$ROOT/utilities/harness-status.sh" "$cwd" "$sid"
    ;;
  worklog)
    cwd=${2:-$PWD}
    AGENT_HOME="${AGENT_HOME:-$ROOT}" \
      AGENT_NOTES_ROOT="${AGENT_NOTES_ROOT:-${WORKLOG_NOTES_ROOT:-}}" \
      WORKLOG_BOARD_APP="${WORKLOG_BOARD_APP:-}" \
      WORKLOG_BOARD_WT="${WORKLOG_BOARD_WT:-}" \
      "$ROOT/utilities/agent-worklog-state.sh" "$cwd"
    ;;
  claim-verify)
    shift
    "$ROOT/adapters/codex/tools/research/claim-verify.sh" "$@"
    ;;
  browser-fetch)
    shift
    "$ROOT/adapters/codex/tools/material/browser-fetch.sh" "$@"
    ;;
  data-script)
    shift
    "$ROOT/adapters/codex/tools/material/data-script.sh" "$@"
    ;;
  figure-gen)
    shift
    "$ROOT/adapters/codex/tools/material/figure-gen.sh" "$@"
    ;;
  pdf-extract)
    shift
    "$ROOT/adapters/codex/tools/material/pdf-extract.sh" "$@"
    ;;
  web-image-search)
    shift
    "$ROOT/adapters/codex/tools/material/web-image-search.sh" "$@"
    ;;
  verification-runner)
    shift
    "$ROOT/adapters/codex/tools/qa/verification-runner.sh" "$@"
    ;;
  design)
    [ "$#" -ge 2 ] || { echo "codex preflight: design requires a file path" >&2; exit 64; }
    file=$2
    AGENT_HOME="$ROOT" bash "$ROOT/hooks/design-postwrite.sh" --file "$file"
    ;;
  visual-harness)
    if [ "$#" -ge 2 ]; then
      shift
      "$ROOT/adapters/codex/tools/design/visual-harness.sh" "$@"
      exit $?
    fi
    cat <<'EOF'
adapter=codex
status=tool-contract
tool_contract=visual-harness
runtime_surface=adapter-owned-visual-harness
tool_contract_check=adapters/codex/bin/preflight.sh visual-harness <file.html>
fallback=preflight.sh visual-harness <file.html>
portable_source=capabilities/autopilot-design.md
note=Codex design capabilities have native Skill guidance and an adapter-owned render/screenshot/console harness. Run it for every design HTML output, then inspect the screenshot before claiming visual completion.
EOF
    ;;
  distill-delta)
    [ "$#" -ge 2 ] || { echo "codex preflight: distill-delta requires a session id" >&2; exit 64; }
    sid=$2
    AGENT_HOME="${AGENT_HOME:-$ROOT}" python3 "$ROOT/tools/memory/mem.py" distill "$sid" --source codex
    ;;
  distill-propose)
    [ "$#" -ge 2 ] || { echo "codex preflight: distill-propose requires a session id" >&2; exit 64; }
    sid=$2
    cwd=${3:-$PWD}
    "$ROOT/adapters/codex/bin/distill-worker.sh" "$sid" "$cwd"
    ;;
  role)
    [ "$#" -ge 2 ] || { echo "codex preflight: role requires a portable role" >&2; exit 64; }
    shift
    "$ROOT/adapters/codex/bin/role-map.sh" "$@"
    ;;
  capability-info)
    [ "$#" -eq 2 ] || { echo "codex preflight: capability-info requires one capability" >&2; exit 64; }
    "$ROOT/adapters/codex/bin/capability-map.sh" "$2"
    ;;
  mode-info)
    [ "$#" -eq 2 ] || { echo "codex preflight: mode-info requires one family/mode" >&2; exit 64; }
    "$ROOT/adapters/codex/bin/mode-map.sh" "$2"
    ;;
  -h|--help|"")
    usage
    exit 0
    ;;
  *)
    echo "codex preflight: unknown command: $cmd" >&2
    usage >&2
    exit 64
    ;;
esac
