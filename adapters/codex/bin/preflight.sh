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
       preflight.sh session-end [cwd] [session-id]
       preflight.sh mode [cwd] [session-id]
       preflight.sh prompt-signal [cwd] [session-id]
       preflight.sh turn-nudge [cwd] [session-id]
       preflight.sh track [cwd] [session-id]
       preflight.sh memory [cwd]
       preflight.sh recall <prompt> [cwd]
       preflight.sh briefing [cwd]
       preflight.sh status [cwd] [session-id]
       preflight.sh permissions
       preflight.sh tui-config
       preflight.sh headless [--check] <worktree>
       preflight.sh dispatch [--dry-run|--register|--start] --worktree <path> --slug <slug> --capability <name> --mode <family/mode> --qa <level> [--prompt-file <file>|--prompt-text <text>] [--jobs <jobs.log>]
       preflight.sh liveness [jobs.log]
       preflight.sh harvest [--jobs <jobs.log>] [--slug <slug>|--worktree <path>] [--status open|done|all] [--mark-done]
       preflight.sh mcp [--check]
       preflight.sh worklog [cwd]
       preflight.sh ui-info
       preflight.sh loop-info <oncall|note|study|drill>
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
       preflight.sh runtime-projection
       preflight.sh doctor [--runtime]

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
  runtime_check=0
  case "${1:-}" in
    "")
      ;;
    --runtime)
      runtime_check=1
      ;;
    *)
      echo "codex preflight: unknown doctor option: $1" >&2
      exit 64
      ;;
  esac

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
  doctor_check native-modes "$ROOT/adapters/codex/bin/sync-native-modes.py" --check || rc=1
  doctor_check hook-bridges python3 -c 'import pathlib, sys; [compile(pathlib.Path(p).read_text(encoding="utf-8"), p, "exec") for p in sys.argv[1:]]' \
    "$ROOT/adapters/codex/hooks/sessionstart-lifecycle.py" \
    "$ROOT/adapters/codex/hooks/sessionend-lifecycle.py" \
    "$ROOT/adapters/codex/hooks/userprompt-lifecycle.py" \
    "$ROOT/adapters/codex/hooks/permissionrequest-lifecycle.py" \
    "$ROOT/adapters/codex/hooks/pretooluse-write-guard.py" \
    "$ROOT/adapters/codex/hooks/posttooluse-design-check.py" \
    "$ROOT/adapters/codex/hooks/posttooluse-read-marker.py" || rc=1
  doctor_check adaptation-boundary doctor_boundary || rc=1
  if [ "$runtime_check" -eq 1 ]; then
    doctor_check runtime-projection "$ROOT/adapters/codex/bin/check-runtime-projection.sh" || rc=1
  else
    printf 'check=runtime-projection:skipped\n'
    printf 'runtime_projection_hint=adapters/codex/bin/preflight.sh doctor --runtime\n'
  fi

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
  AGENT_HOME="$AGENT_ROOT" CODEX_RUNTIME_PROJECTION_SKIP_CLI_DISCOVERY=1 \
    "$ROOT/adapters/codex/bin/check-runtime-projection.sh" || return $?
  printf 'runtime_projection=ok\ncodex_home=%s\n' "$codex_home"
  return 0
}

cmd=${1:-}
case "$cmd" in
  doctor)
    [ "$#" -le 2 ] || { echo "codex preflight: doctor accepts at most one option" >&2; exit 64; }
    doctor "${2:-}"
    ;;
  runtime-projection)
    [ "$#" -eq 1 ] || { echo "codex preflight: runtime-projection accepts no arguments" >&2; exit 64; }
    AGENT_HOME="$AGENT_ROOT" "$ROOT/adapters/codex/bin/check-runtime-projection.sh"
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
    if ! "$ROOT/adapters/codex/bin/capability-map.sh" "$name" >/dev/null 2>/dev/null; then
      printf 'check=failed\nreason=unknown-capability\ncapability=%s\n' "$name"
      exit 64
    fi
    "$ROOT/hooks/spec-skill-gate.sh" --skill "$name" --cwd "$cwd" --session "$sid"
    ;;
  start)
    cwd=${2:-$PWD}
    sid=${3:-codex}
    "$ROOT/utilities/workflow-guard-hook.sh" --event start --cwd "$cwd" --session "$sid" --format text
    ;;
  session-end)
    cwd=${2:-$PWD}
    sid=${3:-codex}
    # Recursion guard: skip the whole session-end pipeline when invoked from
    # within a distiller (the codex exec worker exports MEM_DISTILL=1).
    [ "${MEM_DISTILL:-}" = "1" ] && exit 0
    (cd "$cwd" && AGENT_HOME="$AGENT_ROOT" python3 "$ROOT/tools/memory/mem.py" sync)
    # Automatic session-end distillation is enabled: the codex exec read-only
    # sandbox was verified tool-free (adapters/codex/ADAPTATION.md Distillation
    # Boundary), so default the worker to apply mode. Opt out with
    # CODEX_DISTILL_ENABLE=0.
    AGENT_HOME="$AGENT_ROOT" \
      CODEX_DISTILL_ENABLE="${CODEX_DISTILL_ENABLE:-1}" \
      CODEX_DISTILL_APPLY="${CODEX_DISTILL_APPLY:-1}" \
      CODEX_DISTILL_CONTRACT_ACCEPTED="${CODEX_DISTILL_CONTRACT_ACCEPTED:-1}" \
      "$ROOT/adapters/codex/bin/distill-worker.sh" "$sid" "$cwd"
    ;;
  mode)
    cwd=${2:-$PWD}
    sid=${3:-codex}
    "$ROOT/utilities/workflow-guard-hook.sh" --event prompt --cwd "$cwd" --session "$sid" --format text --toggle-label "preflight.sh track"
    ;;
  prompt-signal)
    cwd=${2:-$PWD}
    sid=${3:-codex}
    status=$(AGENT_ADAPTER=codex "$ROOT/utilities/harness-status.sh" "$cwd" "$sid")
    workflow_state=$(printf '%s\n' "$status" | awk -F= '$1=="workflow_state"{print $2; exit}')
    artifact_root_kind=$(printf '%s\n' "$status" | awk -F= '$1=="artifact_root_kind"{print $2; exit}')
    git_operation=$(printf '%s\n' "$status" | awk -F= '$1=="git_operation"{print $2; exit}')
    headless_open_jobs=$(printf '%s\n' "$status" | awk -F= '$1=="headless_open_jobs"{print $2; exit}')
    printf 'adapter=codex\n'
    printf 'runtime_surface=codex-userprompt-hook-signal\n'
    printf 'hook_event=UserPromptSubmit\n'
    printf 'hook_scope=runtime-hook\n'
    printf 'workflow_state=%s\n' "${workflow_state:-unknown}"
    printf 'artifact_root_kind=%s\n' "${artifact_root_kind:-unknown}"
    printf 'git_operation=%s\n' "${git_operation:-unknown}"
    printf 'headless_open_jobs=%s\n' "${headless_open_jobs:-0}"
    if [ "${workflow_state:-tracked}" = "untracked" ]; then
      printf 'autopilot_route=optional-direct-work-allowed\n'
      printf 'routing_contract=untracked-direct-work\n'
    else
      printf 'autopilot_route=autopilot-required-for-spec-and-nontrivial-work\n'
      printf 'routing_contract=core/WORKFLOW.md\n'
      printf 'routing_action=read-workflow-and-select-codex-skill\n'
      printf 'capability_entrypoints=codex-native-skills-plugin\n'
    fi
    printf 'enforced_hooks=pretool-write-guards,posttool-spec-read-marker,posttool-design-check,session-memory,turn-nudge\n'
    ;;
  turn-nudge)
    cwd=${2:-$PWD}
    sid=${3:-codex}
    [ "${MEM_DISTILL:-}" = "1" ] && exit 0
    [ -n "$sid" ] && [ "$sid" != "default" ] || exit 0
    interval=${MEM_NUDGE_INTERVAL:-10}
    case "$interval" in (*[!0-9]*|"") interval=10 ;; esac
    [ "$interval" -gt 0 ] || interval=10
    store=${MEM_STORE:-$AGENT_ROOT/memory}
    mkdir -p "$store" 2>/dev/null || true
    state="$store/.codex-turn-state-$sid"
    counter=0
    if [ -f "$state" ]; then
      counter=$(sed -n '1p' "$state" 2>/dev/null || echo 0)
    fi
    case "$counter" in (*[!0-9]*|"") counter=0 ;; esac
    counter=$((counter + 1))
    if [ "$counter" -ge "$interval" ]; then
      counter=0
      AGENT_HOME="$AGENT_ROOT" \
        CODEX_DISTILL_ENABLE="${CODEX_DISTILL_ENABLE:-1}" \
        CODEX_DISTILL_APPLY="${CODEX_DISTILL_APPLY:-1}" \
        CODEX_DISTILL_CONTRACT_ACCEPTED="${CODEX_DISTILL_CONTRACT_ACCEPTED:-1}" \
        "$ROOT/adapters/codex/bin/distill-worker.sh" "$sid" "$cwd" >/dev/null 2>/dev/null || true
    fi
    printf '%s\n' "$counter" > "$state" 2>/dev/null || true
    find "$store" -maxdepth 1 -name '.codex-turn-state-*' -mmin +4320 -delete 2>/dev/null || true
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
  tui-config)
    [ "$#" -eq 1 ] || { echo "codex preflight: tui-config accepts no arguments" >&2; exit 64; }
    AGENT_HOME="$AGENT_ROOT" "$ROOT/adapters/codex/bin/apply-tui-config.sh"
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
command_template=codex exec --cd <worktree> --sandbox workspace-write --json -
runtime_projection_requires=agent-harness,AGENTS.md,hooks.json,native-skills,native-agents,native-modes
job_registry=<agent-home>/.dispatch/jobs.log
liveness_surface=codex-session-jsonl-mtime
liveness_check=adapters/codex/bin/preflight.sh liveness [jobs.log]
harvest_check=adapters/codex/bin/preflight.sh harvest [--jobs jobs.log] [--slug slug] [--mark-done]
dispatch_prompt_contract=codex-harness-autopilot-prompt
dispatch_input_validation=capability-info,mode-info,qa-level
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
  ui-info)
    cat <<'EOF'
adapter=codex
runtime_surface=codex-native-ui-boundary
status=partial-native-parity
statusline_surface=codex-native-footer-config
statusline_command=/statusline
statusline_custom_dynamic_fields=unsupported
statusline_config_surface=$CODEX_HOME/config.toml
statusline_fragment=codex_setting/codex-config/tui-statusline.toml
recommended_status_line=project-name,git-branch,context-used,current-dir,model-with-reasoning,five-hour-limit,weekly-limit
recommended_status_line_use_colors=true
title_surface=codex-native-title-config
title_command=/title
hook_status_messages=available-after-hook-trust
harness_status_surface=adapter-owned-preflight-status
harness_status_command=adapters/codex/bin/preflight.sh status [cwd] [session-id]
autopilot_entrypoints=codex-native-skills-plugin
autopilot_auto_routing=instruction-guided-not-claude-slash-router
subagent_surface=codex-native-subagents
subagent_auto_spawn=explicit-or-main-dispatched
note=Codex can configure built-in footer/title items, but it does not expose a Claude-style arbitrary live statusline script surface; use preflight status and hook statusMessage for harness-specific signals.
EOF
    ;;
  loop-info)
    [ "$#" -eq 2 ] || { echo "codex preflight: loop-info requires one loop name" >&2; exit 64; }
    loop=$2
    case "$loop" in
      oncall)
        cat <<'EOF'
adapter=codex
loop=oncall
source=loops/oncall.md
status=manual-contract
runtime_surface=codex-loop-guidance
trigger=external-scheduler-or-manual
action=read-only-report
output=notes/oncall/<date>.md
executable_projection=unsupported-runtime-script
fallback=read-source-and-report-in-main-session
note=Codex may follow the portable oncall guide manually; do not run the Claude-coupled loop script as a Codex-native executable.
EOF
        ;;
      study)
        cat <<'EOF'
adapter=codex
loop=study
source=loops/study.md
status=manual-contract
runtime_surface=codex-loop-guidance
trigger=external-scheduler-or-manual
action=proposal-report-only
output=notes/study/<date>.md
executable_projection=unsupported-runtime-script
fallback=read-source-and-draft-proposal-in-main-session
note=Codex may follow the portable study guide manually; any proposed edits remain proposals until the user accepts them.
EOF
        ;;
      drill)
        cat <<'EOF'
adapter=codex
loop=drill
source=loops/drill/README.md
status=manual-contract
runtime_surface=codex-loop-guidance
trigger=manual-only
action=report-usefulness-before-running
auto_run=unsupported
executable_projection=unsupported-runtime-script
fallback=report-drill-would-be-useful
note=Do not run drill automatically from Codex; it can launch headless runtime sessions and spend tokens.
EOF
        ;;
      note)
        cat <<'EOF'
adapter=codex
loop=note
source=loops/README.md
status=unsupported
runtime_surface=missing-native-loop
trigger=external-scheduler
related_capability=autopilot-note
capability_check=adapters/codex/bin/preflight.sh capability-info autopilot-note
native_capability_surface=codex-native-skill-plugin
scheduler_surface=external-worklog-board
action=not-implemented-in-repo
fallback=worklog-board-or-manual-post-it-flow
note=Codex has an on-demand autopilot-note capability projection, but this repo has no Codex-native scheduled note loop runner.
EOF
        ;;
      *)
        echo "codex preflight: unknown loop: $loop" >&2
        exit 64
        ;;
    esac
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
    if [ "${CODEX_DISTILL_ENABLE:-0}" != "1" ]; then
      cat <<EOF
adapter=codex
status=tool-contract
tool_contract=no-tools-distill-worker
runtime_surface=codex-exec-constrained-proposal
reason=distill-proposal-disabled
delta_surface=adapters/codex/bin/preflight.sh distill-delta <session-id>
enable=CODEX_DISTILL_ENABLE=1
apply_gate=CODEX_DISTILL_APPLY=1+CODEX_DISTILL_CONTRACT_ACCEPTED=1
fallback=inspect-distill-delta-or-enable-after-contract-review
cwd=$cwd
session_id=$sid
EOF
      exit 69
    fi
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
