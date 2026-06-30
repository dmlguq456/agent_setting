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
       preflight.sh permissions
       preflight.sh headless [--check] <worktree>
       preflight.sh liveness [jobs.log]
       preflight.sh mcp [--check]
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
  status)
    cwd=${2:-$PWD}
    sid=${3:-opencode}
    AGENT_ADAPTER=opencode "$ROOT/utilities/harness-status.sh" "$cwd" "$sid"
    ;;
  permissions)
    cat <<'EOF'
adapter=opencode
runtime_surface=opencode-native-permission-config
status=native-runtime-config
permission_model=permission-allow-ask-deny
permission_surface=opencode permission config with allow/ask/deny per tool and per-agent override
plugin_surface=permission.ask and tool.execute hooks
config_surface=$HOME/.config/opencode/opencode.json
claude_allowed_tools=unsupported
guard_contract=preflight-write-plugin-and-explicit-tool-contracts
fallback=configure-opencode-permissions-and-run-preflight-guards
note=Do not port Claude allowedTools into OpenCode; use OpenCode permission config plus adapter preflight/plugin guards.
EOF
    ;;
  headless)
    shift
    check_only=0
    worktree=""
    while [ "$#" -gt 0 ]; do
      case "$1" in
        --check)
          check_only=1
          shift
          ;;
        --*)
          echo "opencode preflight: unknown headless option: $1" >&2
          exit 64
          ;;
        *)
          if [ -z "$worktree" ]; then
            worktree=$1
          else
            echo "opencode preflight: headless accepts one worktree path" >&2
            exit 64
          fi
          shift
          ;;
      esac
    done
    cat <<'EOF'
adapter=opencode
runtime_surface=opencode-run-headless
status=tool-contract
tool_contract=headless-dispatch
tool_contract_check=adapters/opencode/bin/preflight.sh headless --check <worktree>
command_template=opencode run --dir <worktree> --format json --agent <agent> <prompt>
job_registry=<agent-home>/.dispatch/jobs.log
liveness_surface=opencode-sqlite-session-mtime
liveness_check=adapters/opencode/bin/preflight.sh liveness [jobs.log]
constraints=main-only,max-depth-1,register-open-job,explicit-capability-mode-qa,transcript-liveness-required
claude_headless=unsupported
fallback=manual-main-session-or-report-unavailable
EOF
    if [ "$check_only" -eq 0 ]; then
      exit 0
    fi
    [ -n "$worktree" ] || { echo "opencode preflight: headless --check requires a worktree path" >&2; exit 64; }
    if [ ! -d "$worktree" ]; then
      printf 'check=failed\nreason=worktree-not-found\nworktree=%s\n' "$worktree"
      exit 66
    fi
    if ! command -v opencode >/dev/null 2>&1; then
      printf 'check=failed\nreason=opencode-command-unavailable\nworktree=%s\n' "$worktree"
      exit 69
    fi
    if ! git -C "$worktree" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
      printf 'check=failed\nreason=not-a-git-worktree\nworktree=%s\n' "$worktree"
      exit 65
    fi
    printf 'check=ok\nworktree=%s\n' "$worktree"
    ;;
  liveness)
    jobs=${2:-"${AGENT_HOME:-$ROOT}/.dispatch/jobs.log"}
    AGENT_HOME="${AGENT_HOME:-$ROOT}" "$ROOT/adapters/opencode/bin/dispatch-liveness.py" "$jobs"
    ;;
  mcp)
    shift
    check_only=0
    while [ "$#" -gt 0 ]; do
      case "$1" in
        --check)
          check_only=1
          shift
          ;;
        --*)
          echo "opencode preflight: unknown mcp option: $1" >&2
          exit 64
          ;;
        *)
          echo "opencode preflight: mcp accepts no positional arguments" >&2
          exit 64
          ;;
      esac
    done
    cat <<'EOF'
adapter=opencode
runtime_surface=opencode-native-mcp
status=native-runtime-config
mcp_surface=opencode mcp
config_surface=$HOME/.config/opencode/opencode.json
design_mcp_projection=unsupported
claude_settings_mcp=unsupported
tool_contract_check=adapters/opencode/bin/preflight.sh mcp --check
fallback=use-adapter-visual-harness-or-report-mcp-unavailable
note=Do not copy Claude settings.json MCP registrations or project tools/design-mcp wholesale into OpenCode.
EOF
    if [ "$check_only" -eq 0 ]; then
      exit 0
    fi
    if command -v opencode >/dev/null 2>&1 && opencode mcp --help >/dev/null 2>&1; then
      printf 'check=ok\n'
    else
      printf 'check=failed\nreason=opencode-mcp-unavailable\n'
      exit 69
    fi
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
    "$ROOT/adapters/opencode/tools/research/claim-verify.sh" "$@"
    ;;
  browser-fetch)
    shift
    "$ROOT/adapters/opencode/tools/material/browser-fetch.sh" "$@"
    ;;
  data-script)
    shift
    "$ROOT/adapters/opencode/tools/material/data-script.sh" "$@"
    ;;
  figure-gen)
    shift
    "$ROOT/adapters/opencode/tools/material/figure-gen.sh" "$@"
    ;;
  pdf-extract)
    shift
    "$ROOT/adapters/opencode/tools/material/pdf-extract.sh" "$@"
    ;;
  web-image-search)
    shift
    "$ROOT/adapters/opencode/tools/material/web-image-search.sh" "$@"
    ;;
  verification-runner)
    shift
    "$ROOT/adapters/opencode/tools/qa/verification-runner.sh" "$@"
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
