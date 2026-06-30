#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if command -v git >/dev/null 2>&1 && ROOT=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null); then
  :
else
  ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd)
fi

agent_home() {
  if [ -n "${AGENT_HOME:-}" ] && [ -f "$AGENT_HOME/core/CORE.md" ]; then
    printf '%s\n' "$AGENT_HOME"
  else
    printf '%s\n' "$ROOT"
  fi
}

AGENT_ROOT=$(agent_home)

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
       preflight.sh dispatch [--dry-run|--register|--start] --worktree <path> --slug <slug> --capability <name> --mode <family/mode> --qa <level> [--prompt-file <file>|--prompt-text <text>] [--jobs <jobs.log>]
       preflight.sh liveness [jobs.log]
       preflight.sh harvest [--jobs <jobs.log>] [--slug <slug>|--worktree <path>] [--status open|done|all] [--mark-done]
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
       preflight.sh doctor

Runs portable checks that Codex can call without consuming Claude hook JSON or
settings.json.
EOF
}

doctor_check() {
  name=$1
  shift
  if "$@" >/dev/null 2>&1; then
    printf 'check=%s:ok\n' "$name"
    return 0
  fi
  printf 'check=%s:failed\n' "$name"
  return 1
}

doctor_boundary() {
  lock="${TMPDIR:-/tmp}/agent-setting-adaptation-boundary.lock"
  tries=0
  while ! mkdir "$lock" 2>/dev/null; do
    tries=$((tries + 1))
    if [ "$tries" -ge 100 ]; then
      return 1
    fi
    sleep 0.1
  done
  trap 'rmdir "$lock" 2>/dev/null || true' EXIT HUP INT TERM
  "$ROOT/tools/check-adaptation-boundary.sh"
  rc=$?
  rmdir "$lock" 2>/dev/null || true
  trap - EXIT HUP INT TERM
  return "$rc"
}

doctor() {
  rc=0
  printf 'adapter=codex\n'
  printf 'runtime_surface=adapter-readiness-doctor\n'
  printf 'agent_home=%s\n' "$AGENT_ROOT"
  if command -v codex >/dev/null 2>&1; then
    printf 'runtime_cli=available\n'
  else
    printf 'runtime_cli=unavailable\n'
  fi

  doctor_check manifest python3 "$ROOT/tools/build-manifest.py" --check || rc=1
  doctor_check native-skills "$ROOT/adapters/codex/bin/sync-native-skills.py" --check || rc=1
  doctor_check native-plugin "$ROOT/adapters/codex/bin/sync-native-plugin.py" --check || rc=1
  doctor_check native-agents "$ROOT/adapters/codex/bin/sync-native-agents.py" --check || rc=1
  doctor_check hook-bridges python3 -c 'import pathlib, sys; [compile(pathlib.Path(p).read_text(encoding="utf-8"), p, "exec") for p in sys.argv[1:]]' \
    "$ROOT/adapters/codex/hooks/sessionstart-lifecycle.py" \
    "$ROOT/adapters/codex/hooks/userprompt-lifecycle.py" \
    "$ROOT/adapters/codex/hooks/pretooluse-write-guard.py" \
    "$ROOT/adapters/codex/hooks/posttooluse-design-check.py" \
    "$ROOT/adapters/codex/hooks/posttooluse-read-marker.py" || rc=1
  doctor_check adaptation-boundary doctor_boundary || rc=1

  if [ "$rc" -eq 0 ]; then
    printf 'status=ok\n'
  else
    printf 'status=failed\n'
  fi
  return "$rc"
}

codex_runtime_projection_check() {
  codex_home=${CODEX_HOME:-${HOME:-}/.codex}
  if [ -z "$codex_home" ]; then
    printf 'check=failed\nreason=codex-home-unset\n'
    return 69
  fi
  harness="$codex_home/agent-harness"
  if [ ! -f "$harness/core/CORE.md" ]; then
    printf 'check=failed\nreason=codex-agent-harness-missing\ncodex_home=%s\nexpected=%s\n' "$codex_home" "$harness"
    return 69
  fi
  if [ ! -f "$codex_home/AGENTS.md" ]; then
    printf 'check=failed\nreason=codex-bootstrap-missing\ncodex_home=%s\nexpected=%s\n' "$codex_home" "$codex_home/AGENTS.md"
    return 69
  fi
  if [ ! -f "$codex_home/hooks.json" ]; then
    printf 'check=failed\nreason=codex-hooks-missing\ncodex_home=%s\nexpected=%s\n' "$codex_home" "$codex_home/hooks.json"
    return 69
  fi
  if [ ! -f "$codex_home/skills/autopilot-code/SKILL.md" ]; then
    printf 'check=failed\nreason=codex-native-skills-missing\ncodex_home=%s\nexpected=%s\n' "$codex_home" "$codex_home/skills/autopilot-code/SKILL.md"
    return 69
  fi
  if [ ! -f "$codex_home/agents/qa-team.toml" ]; then
    printf 'check=failed\nreason=codex-native-agents-missing\ncodex_home=%s\nexpected=%s\n' "$codex_home" "$codex_home/agents/qa-team.toml"
    return 69
  fi
  if rg -q 'adapters/claude|claude_setting|settings\.json|statusline\.sh|CLAUDE\.md|track-toggle\.sh|agent-modes|allowedTools|/\.claude/' \
    "$codex_home/hooks.json" "$codex_home/skills/autopilot-code/SKILL.md" "$codex_home/agents/qa-team.toml" 2>/dev/null; then
    printf 'check=failed\nreason=codex-runtime-projection-exposes-claude-surface\ncodex_home=%s\n' "$codex_home"
    return 69
  fi
  printf 'runtime_projection=ok\ncodex_home=%s\n' "$codex_home"
  return 0
}

cmd=${1:-}
case "$cmd" in
  doctor)
    doctor
    ;;
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
    (cd "$cwd" && AGENT_HOME="$AGENT_ROOT" python3 "$ROOT/tools/memory/mem.py" inject)
    ;;
  recall)
    [ "$#" -ge 2 ] || { echo "codex preflight: recall requires prompt text" >&2; exit 64; }
    prompt=$2
    cwd=${3:-$PWD}
    AGENT_HOME="$AGENT_ROOT" "$ROOT/hooks/mem-recall-inject.sh" --prompt "$prompt" --cwd "$cwd" --format text
    ;;
  briefing)
    cwd=${2:-$PWD}
    AGENT_HOME="$AGENT_ROOT" bash "$ROOT/hooks/mem-briefing-inject.sh" --cwd "$cwd" --format text
    ;;
  status)
    cwd=${2:-$PWD}
    sid=${3:-codex}
    AGENT_ADAPTER=codex "$ROOT/utilities/harness-status.sh" "$cwd" "$sid"
    ;;
  permissions)
    cat <<'EOF'
adapter=codex
runtime_surface=codex-native-approval-sandbox
status=native-runtime-config
permission_model=approval-policy+sandbox
approval_surface=codex --ask-for-approval <untrusted|on-request|never>
sandbox_surface=codex --sandbox <read-only|workspace-write|danger-full-access>
config_surface=$CODEX_HOME/config.toml
claude_allowed_tools=unsupported
guard_contract=preflight-write-hooks-and-explicit-tool-contracts
fallback=configure-codex-approval-sandbox-and-run-preflight-guards
note=Do not port Claude allowedTools into Codex; use Codex approval/sandbox settings plus adapter preflight guards.
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
          echo "codex preflight: unknown headless option: $1" >&2
          exit 64
          ;;
        *)
          if [ -z "$worktree" ]; then
            worktree=$1
          else
            echo "codex preflight: headless accepts one worktree path" >&2
            exit 64
          fi
          shift
          ;;
      esac
    done
    cat <<'EOF'
adapter=codex
runtime_surface=codex-exec-headless
status=tool-contract
tool_contract=headless-dispatch
tool_contract_check=adapters/codex/bin/preflight.sh headless --check <worktree>
command_template=codex exec --cd <worktree> --sandbox workspace-write --ask-for-approval never --json -
job_registry=<agent-home>/.dispatch/jobs.log
liveness_surface=codex-session-jsonl-mtime
liveness_check=adapters/codex/bin/preflight.sh liveness [jobs.log]
harvest_check=adapters/codex/bin/preflight.sh harvest [--jobs jobs.log] [--slug slug] [--mark-done]
constraints=main-only,max-depth-1,register-open-job,explicit-capability-mode-qa,transcript-liveness-required
claude_headless=unsupported
fallback=manual-main-session-or-report-unavailable
EOF
    if [ "$check_only" -eq 0 ]; then
      exit 0
    fi
    [ -n "$worktree" ] || { echo "codex preflight: headless --check requires a worktree path" >&2; exit 64; }
    if [ ! -d "$worktree" ]; then
      printf 'check=failed\nreason=worktree-not-found\nworktree=%s\n' "$worktree"
      exit 66
    fi
    if ! command -v codex >/dev/null 2>&1; then
      printf 'check=failed\nreason=codex-command-unavailable\nworktree=%s\n' "$worktree"
      exit 69
    fi
    if ! git -C "$worktree" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
      printf 'check=failed\nreason=not-a-git-worktree\nworktree=%s\n' "$worktree"
      exit 65
    fi
    codex_runtime_projection_check
    printf 'check=ok\nworktree=%s\n' "$worktree"
    ;;
  liveness)
    jobs=${2:-"$AGENT_ROOT/.dispatch/jobs.log"}
    AGENT_HOME="$AGENT_ROOT" "$ROOT/adapters/codex/bin/dispatch-liveness.py" "$jobs"
    ;;
  harvest)
    shift
    AGENT_HOME="$AGENT_ROOT" "$ROOT/adapters/codex/bin/dispatch-harvest.py" "$@"
    ;;
  dispatch)
    shift
    AGENT_HOME="$AGENT_ROOT" "$ROOT/adapters/codex/bin/dispatch-headless.py" "$@"
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
          echo "codex preflight: unknown mcp option: $1" >&2
          exit 64
          ;;
        *)
          echo "codex preflight: mcp accepts no positional arguments" >&2
          exit 64
          ;;
      esac
    done
    cat <<'EOF'
adapter=codex
runtime_surface=codex-native-mcp
status=native-runtime-config
mcp_surface=codex mcp
config_surface=$CODEX_HOME/config.toml
design_mcp_projection=unsupported
claude_settings_mcp=unsupported
tool_contract_check=adapters/codex/bin/preflight.sh mcp --check
fallback=use-adapter-visual-harness-or-report-mcp-unavailable
note=Do not copy Claude settings.json MCP registrations or project tools/design-mcp wholesale into Codex.
EOF
    if [ "$check_only" -eq 0 ]; then
      exit 0
    fi
    if command -v codex >/dev/null 2>&1 && codex mcp --help >/dev/null 2>&1; then
      printf 'check=ok\n'
    else
      printf 'check=failed\nreason=codex-mcp-unavailable\n'
      exit 69
    fi
    ;;
  worklog)
    cwd=${2:-$PWD}
    AGENT_HOME="$AGENT_ROOT" \
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
    AGENT_HOME="$AGENT_ROOT" bash "$ROOT/hooks/design-postwrite.sh" --file "$file"
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
    AGENT_HOME="$AGENT_ROOT" python3 "$ROOT/tools/memory/mem.py" distill "$sid" --source codex
    ;;
  distill-propose)
    [ "$#" -ge 2 ] || { echo "codex preflight: distill-propose requires a session id" >&2; exit 64; }
    sid=$2
    cwd=${3:-$PWD}
    AGENT_HOME="$AGENT_ROOT" "$ROOT/adapters/codex/bin/distill-worker.sh" "$sid" "$cwd"
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
