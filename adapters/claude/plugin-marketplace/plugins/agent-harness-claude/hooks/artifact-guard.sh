#!/usr/bin/env bash
# PreToolUse(Edit|Write|MultiEdit): enforce only artifact creation order.
# The canonical artifact root is .agent_reports; .claude_reports is a legacy alias.
# Modes: 📌tracked (default) and ⚡untracked (session flag bypasses all checks).
# /track toggles the mode; SessionStart garbage-collects stale flags.
#
# In tracked mode, a new artifact requires its upstream artifact (exit 2 otherwise):
#   · new spec (prd/stack/ship/api_contract/data_model/ui_flow) ← research/ or analysis_project/
#   · new plan ← spec/
#   · new documents ← research/ or analysis_project/
# Non-blocking by convention: edits to existing artifacts, source code,
# experiments/, user_profile/, README, assets, and _internal.
# WORKFLOW.md §0 is the source of truth for tracked mode.
set -euo pipefail

fp=""
sid=""
toggle_label="${ARTIFACT_GUARD_TOGGLE_LABEL:-/track}"
route_file="${AGENT_ROUTE_FILE:-}"
route_id="${AGENT_ROUTE_ID:-unknown}"
route_node="${AGENT_ROUTE_NODE:-}"

route_failure(){
  reason=$1
  python3 - "$reason" "$route_id" "$route_file" "${fp:-}" <<'PY' >&2
import json,sys
print(json.dumps({"status":"blocked","reason":sys.argv[1],"route_id":sys.argv[2],"route_file":sys.argv[3],"target":sys.argv[4]},sort_keys=True))
PY
}

if [ "$#" -gt 0 ]; then
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --file)
        [ "$#" -ge 2 ] || { echo "artifact-guard: --file requires a path" >&2; exit 64; }
        fp="$2"; shift 2 ;;
      --session)
        [ "$#" -ge 2 ] || { echo "artifact-guard: --session requires an id" >&2; exit 64; }
        sid="$2"; shift 2 ;;
      --help|-h)
        echo "usage: artifact-guard.sh --file <path> [--session <id>]"
        exit 0 ;;
      *)
        echo "artifact-guard: unknown argument: $1" >&2
        exit 64 ;;
    esac
  done
else
  input=$(cat)
  eval "$(printf '%s' "$input" | python3 -c '
import sys, json, shlex
try: d = json.load(sys.stdin)
except Exception: d = {}
ti = d.get("tool_input") or {}
print("FP="+shlex.quote(ti.get("file_path","") or ""))
print("SID="+shlex.quote(d.get("session_id","") or ""))
' 2>/dev/null)"
  fp="${FP:-}"; sid="${SID:-}"
fi

[ -z "$fp" ] && exit 0

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ARTIFACT_ROOT_RESOLVER="$SCRIPT_DIR/../utilities/artifact-root.sh"

case "$fp" in
  /*) ;;
  *) fp="$PWD/$fp" ;;
esac

# ---- Source-only linked worktree gate ----
# A tracked artifact snapshot can exist in every Git worktree. It is read-only
# shadow state: only the canonical artifact root selected by artifact-root.sh is
# writable. Run this before the _internal snapshot exemption.
case "$fp" in
  */.agent_reports/*) local_project=${fp%%/.agent_reports/*}; local_artifact="$local_project/.agent_reports" ;;
  */.claude_reports/*) local_project=${fp%%/.claude_reports/*}; local_artifact="$local_project/.claude_reports" ;;
  *) local_project=""; local_artifact="" ;;
esac
if [ -n "$local_project" ]; then
  canonical=$("$ARTIFACT_ROOT_RESOLVER" "$local_project" 2>/dev/null) || {
    [ -z "$route_file" ] || route_failure "canonical-artifact-root-unresolved"
    echo "⛔ Cannot resolve the canonical artifact root; artifact writes fail closed: $fp" >&2
    exit 2
  }
  if [ -d "$local_artifact" ]; then
    local_artifact=$(CDPATH= cd -- "$local_artifact" 2>/dev/null && pwd -P) || {
      [ -z "$route_file" ] || route_failure "artifact-target-normalization-failed"
      echo "⛔ Cannot normalize artifact write target: $fp" >&2
      exit 2
    }
  else
    local_parent=$(dirname "$local_artifact")
    local_parent=$(CDPATH= cd -- "$local_parent" 2>/dev/null && pwd -P) || {
      [ -z "$route_file" ] || route_failure "artifact-target-normalization-failed"
      echo "⛔ Cannot normalize artifact write target: $fp" >&2
      exit 2
    }
    local_artifact="$local_parent/$(basename "$local_artifact")"
  fi
  if [ "$local_artifact" != "$canonical" ]; then
    [ -z "$route_file" ] || route_failure "canonical-artifact-root-mismatch"
    printf '⛔ Task worktrees are source-only; agent artifacts must use the canonical root.\n   requested=%s\n   canonical=%s\n' "$fp" "$canonical" >&2
    exit 2
  fi
fi

case "$fp" in */_internal/*) exit 0 ;; esac   # Machine-managed canonical snapshot.

# ---- Project root containing the canonical artifact root ----
root=$local_project
[ -z "$root" ] && exit 0
cr=$canonical

# A route-backed spec write must declare spec_touch and assign a spec scope to
# the active node. This is checked before the creation-order rule so a late
# guard collision is route-addressable rather than a silent generic denial.
case "$fp" in
  "$cr"/spec/*)
    if [ -n "$route_file" ]; then
      if ! python3 - "$route_file" "$route_id" "$route_node" <<'PY'
import json,sys
from pathlib import Path
try:
    route=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    node=next(row for row in route["nodes"] if row["id"]==sys.argv[3])
    roots=[scope[:-3] if scope.endswith("/**") else scope for scope in node["write_scope"]]
    ok=route.get("route_id")==sys.argv[2] and route.get("spec_touch") is True and any(root=="spec" or root.startswith("spec/") for root in roots)
except Exception:
    ok=False
raise SystemExit(0 if ok else 1)
PY
      then
        route_failure "spec-touch-not-declared-or-outside-node-scope"
        exit 2
      fi
    fi ;;
esac

# ---- ⚡untracked bypass (per-session flag isolates concurrent sessions) ----
flagbase="$cr/.untracked"; [ -d "$cr" ] || flagbase="$root/.untracked"
[ -n "$sid" ] && flag="$flagbase.$sid" || flag="$flagbase"
[ -f "$flag" ] && exit 0

# ---- Existence helpers ----
has_spec(){ [ -f "$cr/spec/pipeline_state.yaml" ] || ls "$cr"/spec/*/pipeline_state.yaml >/dev/null 2>&1; }
has_research(){ ls -A "$cr/research" >/dev/null 2>&1 || ls -A "$cr/analysis_project" >/dev/null 2>&1; }
block(){ [ -z "$route_file" ] || route_failure "artifact-order-guard-blocked"; printf '───────────────────────────────────────────\n⛔ %s\n   %s\n───────────────────────────────────────────\n   Bypass: %s → ⚡untracked (this session only)\n' "$1" "$2" "$toggle_label" >&2; exit 2; }

base=$(basename "$fp")

# ---- (1) Creation-order gate: new artifacts require upstream artifacts ----
# Existing-artifact edits remain allowed because the hook cannot distinguish
# owner-Skill edits from direct edits. Only an ordering violation is blocked.
case "$fp" in
  */.agent_reports/spec/*|*/.claude_reports/spec/*)
    case "$base" in
      prd.md|stack.md|stack_decision.md|ship.md|api_contract.md|data_model.md|ui_flow.md)
        [ -f "$fp" ] || has_research || block "Research or analysis is required before a new spec ($base)" "→ run autopilot-research or analyze-project first" ;;
    esac ;;
  */.agent_reports/plans/*|*/.claude_reports/plans/*)
    [ -f "$fp" ] || has_spec || block "A spec is required before a new plan" "→ run autopilot-spec first" ;;
  */.agent_reports/documents/*|*/.claude_reports/documents/*)
    [ -f "$fp" ] || has_research || block "Research or analysis is required before a new document ($base)" "→ run autopilot-research or analyze-project first" ;;
esac

# Source-code edits are not blocked here. UserPromptSubmit routing and
# convention steer them through autopilot-code.
exit 0
