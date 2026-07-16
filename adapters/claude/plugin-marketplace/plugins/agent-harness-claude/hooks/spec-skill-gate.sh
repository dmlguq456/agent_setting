#!/bin/sh
# PreToolUse(Skill): when a spec-changing Skill runs in a spec-backed cwd,
# deny it unless this session has actually read prd.md (marker present).
# Portable CLI: spec-skill-gate.sh --skill <name> [--cwd <dir>] [--session <id>] [--agent-home <dir>]
# Also deny when prd.md changed after that read, forcing a fresh read.
# This is a verifiable hard gate rather than self-reporting. POSIX sh, no jq.
# autopilot-note is excluded because digest work does not change the blueprint.

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
AGENT_HOME="${AGENT_HOME:-$("$SCRIPT_DIR/../utilities/agent-home.sh")}"
ARTIFACT_ROOT_RESOLVER="$SCRIPT_DIR/../utilities/artifact-root.sh"

usage() {
  cat <<'EOF'
usage: spec-skill-gate.sh --skill <name> [--cwd <dir>] [--session <id>] [--agent-home <dir>]
       spec-skill-gate.sh --capability <name> [--cwd <dir>] [--session <id>] [--agent-home <dir>]

Without arguments, reads Claude hook JSON from stdin.
EOF
}

find_prd() {
  dir=$1
  candidates=""
  root=""
  while [ ! -d "$dir" ]; do
    parent=$(dirname "$dir")
    [ "$parent" = "$dir" ] && return 0
    dir=$parent
  done
  dir=$(CDPATH= cd -- "$dir" && pwd -P)
  artifact_root=$("$ARTIFACT_ROOT_RESOLVER" "$dir" 2>/dev/null) || return 0

  if [ -f "$artifact_root/spec/prd.md" ]; then
    candidates="$artifact_root/spec/prd.md"
  fi

  for d in "$artifact_root"/spec/*/; do
    [ -d "$d" ] || continue
    d="${d%/}"
    slug=$(basename "$d")
    [ "$slug" = "_internal" ] && continue
    [ -f "$d/prd.md" ] || continue
    if [ -z "$candidates" ]; then
      candidates="$d/prd.md"
    else
      candidates="$candidates
$d/prd.md"
    fi
  done

  [ -n "$candidates" ] && root=$(dirname "$artifact_root")
}

check_gate() {
  skill=$1
  cwd=$2
  sid=$3

  if [ -d "$cwd" ]; then
    cwd=$(CDPATH= cd -- "$cwd" && pwd -P)
  fi

  case "$skill" in
    autopilot-code|autopilot-spec) ;;
    *) return 0 ;;   # Capability is not spec-governed.
  esac

  find_prd "$cwd"
  [ -z "$candidates" ] && return 0   # Not a spec-backed project.

  key=$(printf '%s' "$root" | sed 's#[/ ]#_#g')

  any_marker=0
  unsatisfied=""
  total=0
  IFS_OLD=$IFS
  IFS='
'
  for candidate in $candidates; do
    IFS=$IFS_OLD
    total=$((total + 1))
    parent=$(dirname "$candidate")
    parent_base=$(basename "$parent")
    if [ "$parent_base" = spec ]; then
      marker_name="${sid}__${key}"
    else
      slug_key=$(printf '%s' "$parent_base" | sed 's#[/ ]#_#g')
      marker_name="${sid}__${key}__${slug_key}"
    fi
    marker="$AGENT_HOME/.spec-grounding/${marker_name}"
    cur=$(stat -c %Y "$candidate" 2>/dev/null || echo 0)
    if [ -f "$marker" ]; then
      any_marker=1
      read_mtime=$(cat "$marker" 2>/dev/null || echo 0)
      if [ "$cur" -le "$read_mtime" ]; then
        IFS=$IFS_OLD
        return 0   # This candidate is satisfied — ANY satisfied candidate passes the gate.
      fi
    fi
    if [ -z "$unsatisfied" ]; then
      unsatisfied="$candidate"
    else
      unsatisfied="$unsatisfied
$candidate"
    fi
    IFS='
'
  done
  IFS=$IFS_OLD

  if [ "$total" -eq 1 ]; then
    prd="$candidates"
    if [ "$any_marker" -eq 1 ]; then
      reason="prd.md changed after the most recent Read marker. Read $prd again, then retry."
    else
      reason="This cwd is spec-backed, but prd.md was not read in this session. Read $prd directly with the Read tool, then retry. A code comment or brief quotation does not satisfy the gate."
    fi
    return 2
  fi

  list=$(printf '%s' "$unsatisfied" | tr '\n' ',' | sed 's/,/, /g')
  if [ "$any_marker" -eq 1 ]; then
    reason="One or more governing spec candidates changed after the most recent Read marker: $list. Read the one governing the declared work scope again, then retry. A code comment or brief quotation does not satisfy the gate."
  else
    reason="This cwd is spec-backed, but no governing spec candidate was read in this session: $list. Read the one governing the declared work scope directly with the Read tool, then retry. A code comment or brief quotation does not satisfy the gate."
  fi
  return 2
}

deny_json() {
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$1"
  exit 0
}

if [ "$#" -gt 0 ]; then
  skill=""
  cwd=$PWD
  sid="nosession"
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --skill|--capability)
        [ "$#" -ge 2 ] || { echo "spec-skill-gate: $1 requires a name" >&2; exit 64; }
        skill=$2
        shift 2
        ;;
      --cwd)
        [ "$#" -ge 2 ] || { echo "spec-skill-gate: --cwd requires a dir" >&2; exit 64; }
        cwd=$2
        shift 2
        ;;
      --session)
        [ "$#" -ge 2 ] || { echo "spec-skill-gate: --session requires an id" >&2; exit 64; }
        sid=$2
        shift 2
        ;;
      --agent-home)
        [ "$#" -ge 2 ] || { echo "spec-skill-gate: --agent-home requires a dir" >&2; exit 64; }
        AGENT_HOME=$2
        shift 2
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        echo "spec-skill-gate: unknown argument: $1" >&2
        usage >&2
        exit 64
        ;;
    esac
  done
  [ -n "$skill" ] || { echo "spec-skill-gate: --skill is required" >&2; exit 64; }
  reason=""
  check_gate "$skill" "$cwd" "$sid"
  rc=$?
  if [ "$rc" -eq 0 ]; then
    exit 0
  fi
  [ "$rc" -eq 2 ] && printf '%s\n' "$reason" >&2
  exit "$rc"
fi

input=$(cat 2>/dev/null)
[ -z "$input" ] && exit 0

skill=$(printf '%s' "$input" | grep -o '"skill"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"skill"[[:space:]]*:[[:space:]]*"//; s/"$//')
sid=$(printf '%s' "$input" | grep -o '"session_id"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"session_id"[[:space:]]*:[[:space:]]*"//; s/"$//')
[ -z "$sid" ] && sid="nosession"

reason=""
check_gate "$skill" "$PWD" "$sid"
rc=$?
if [ "$rc" -eq 0 ]; then
  exit 0
fi
[ "$rc" -eq 2 ] && deny_json "$reason"
exit 0
