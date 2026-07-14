#!/usr/bin/env bash
# workflow-guard-hook — workflow-mode signal plus stale-flag GC.
#   UserPromptSubmit: expose the runtime-only 📌tracked versus ⚡untracked flag
#                     for projects with an artifact root.
#   SessionStart: remove stale per-session untracked flags only.
# The runtime bootstrap and domain instructions, not this hook, own reading
# WORKFLOW.md and continuity memory.
# Portable CLI:
#   workflow-guard-hook.sh --event prompt [--cwd <dir>] [--session <id>] [--format text|claude-json] [--toggle-label <text>]
#   workflow-guard-hook.sh --event start  [--cwd <dir>] [--session <id>] [--format text|claude-json]
# Register through adapter-native session-start and prompt-submit surfaces.
set -euo pipefail

usage() {
  cat <<'EOF'
usage: workflow-guard-hook.sh --event prompt|start [--cwd <dir>] [--session <id>] [--format text|claude-json] [--toggle-label <text>]

Without arguments, reads Claude hook JSON from stdin and emits Claude hook JSON.
EOF
}

EVENT=""
SID=""
MODE="hook"
FORMAT="claude-json"
CWD="$PWD"
TOGGLE_LABEL="/track"

if [ "$#" -gt 0 ]; then
  MODE="cli"
  FORMAT="text"
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --event)
        [ "$#" -ge 2 ] || { echo "workflow-guard-hook: --event requires a value" >&2; exit 64; }
        case "$2" in
          prompt|UserPromptSubmit) EVENT="UserPromptSubmit" ;;
          start|SessionStart) EVENT="SessionStart" ;;
          *) echo "workflow-guard-hook: unknown event: $2" >&2; exit 64 ;;
        esac
        shift 2
        ;;
      --cwd)
        [ "$#" -ge 2 ] || { echo "workflow-guard-hook: --cwd requires a dir" >&2; exit 64; }
        CWD=$2
        shift 2
        ;;
      --session)
        [ "$#" -ge 2 ] || { echo "workflow-guard-hook: --session requires an id" >&2; exit 64; }
        SID=$2
        shift 2
        ;;
      --format)
        [ "$#" -ge 2 ] || { echo "workflow-guard-hook: --format requires a value" >&2; exit 64; }
        case "$2" in text|claude-json) FORMAT=$2 ;; *) echo "workflow-guard-hook: unknown format: $2" >&2; exit 64 ;; esac
        shift 2
        ;;
      --toggle-label)
        [ "$#" -ge 2 ] || { echo "workflow-guard-hook: --toggle-label requires a value" >&2; exit 64; }
        TOGGLE_LABEL=$2
        shift 2
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        echo "workflow-guard-hook: unknown argument: $1" >&2
        usage >&2
        exit 64
        ;;
    esac
  done
  [ -n "$EVENT" ] || { echo "workflow-guard-hook: --event is required" >&2; exit 64; }
else
  input=$(cat 2>/dev/null || true)
  eval "$(printf '%s' "$input" | python3 -c '
import json, sys, shlex
try: d = json.load(sys.stdin)
except Exception: d = {}
print("EVENT="+shlex.quote(d.get("hook_event_name","") or ""))
print("SID="+shlex.quote(d.get("session_id","") or ""))
' 2>/dev/null || true)"
  EVENT="${EVENT:-}"; SID="${SID:-}"
fi

# Detect a project cwd through git or an artifact root.
is_project=0
if command -v git >/dev/null 2>&1 && git -C "$CWD" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  is_project=1
fi

# Walk upward to locate `.agent_reports/` or legacy `.claude_reports/`.
d="$CWD"; cr_root=""; reports_dir=""
for _ in $(seq 1 40); do
  [ -d "$d/.agent_reports" ] && { cr_root="$d"; reports_dir=".agent_reports"; break; }
  [ -d "$d/.claude_reports" ] && { cr_root="$d"; reports_dir=".claude_reports"; break; }
  { [ "$d" = "/" ] || [ "$d" = "$HOME" ]; } && break
  d=$(dirname "$d")
done
[ -n "$cr_root" ] && is_project=1

# Resolve the per-session ⚡untracked flag.
untracked=0
if [ -n "$cr_root" ]; then
  flag="$cr_root/$reports_dir/.untracked"; [ -n "$SID" ] && flag="$flag.$SID"
  [ -f "$flag" ] && untracked=1
fi

emit() {  # $1 = hookEventName; stdin = context body
  local ctx j
  ctx=$(cat)
  if [ "$FORMAT" = "text" ]; then
    printf '%s\n' "$ctx"
    return 0
  fi
  j=$(printf '%s' "$ctx" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')
  printf '{"hookSpecificOutput":{"hookEventName":"%s","additionalContext":%s}}\n' "$1" "$j"
}

# ============================================================
# UserPromptSubmit — emit a thin mode reminder.
# ============================================================
if [ "$EVENT" = "UserPromptSubmit" ]; then
  # Without an artifact root, workflow tracking does not apply.
  [ -z "$cr_root" ] && exit 0
  # Emit both modes explicitly so the agent can apply the current contract.
  if [ "$untracked" = "1" ]; then
    touch "$flag" 2>/dev/null || true   # Heartbeat keeps active long-lived sessions out of GC.
    emit UserPromptSubmit <<EOF
🧭 ⚡untracked — WORKFLOW routing is suspended; direct edits are allowed · restore tracked mode with ${TOGGLE_LABEL}
EOF
  else
    emit UserPromptSubmit <<'EOF'
🧭 📌tracked — route governed work through autopilot-*; direct work is limited to one-off, minor-doc, and quick-experiment exceptions · WORKFLOW §0/§7
EOF
  fi
  exit 0
fi

# ============================================================
# SessionStart (default): remove ⚡untracked flags inactive for over three days.
# Prompt heartbeats preserve active long-lived sessions. The runtime bootstrap
# and domain instructions own WORKFLOW/memory reads; this hook injects neither.
# ============================================================
if [ -n "$cr_root" ]; then
  find "$cr_root/$reports_dir" -maxdepth 1 -name '.untracked.*' -mmin +4320 -delete 2>/dev/null || true
fi
exit 0
