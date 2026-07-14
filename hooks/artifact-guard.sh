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
    echo "⛔ Cannot resolve the canonical artifact root; artifact writes fail closed: $fp" >&2
    exit 2
  }
  if [ -d "$local_artifact" ]; then
    local_artifact=$(CDPATH= cd -- "$local_artifact" 2>/dev/null && pwd -P) || {
      echo "⛔ Cannot normalize artifact write target: $fp" >&2
      exit 2
    }
  else
    local_parent=$(dirname "$local_artifact")
    local_parent=$(CDPATH= cd -- "$local_parent" 2>/dev/null && pwd -P) || {
      echo "⛔ Cannot normalize artifact write target: $fp" >&2
      exit 2
    }
    local_artifact="$local_parent/$(basename "$local_artifact")"
  fi
  if [ "$local_artifact" != "$canonical" ]; then
    printf '⛔ Task worktrees are source-only; agent artifacts must use the canonical root.\n   requested=%s\n   canonical=%s\n' "$fp" "$canonical" >&2
    exit 2
  fi
fi

case "$fp" in */_internal/*) exit 0 ;; esac   # Machine-managed canonical snapshot.

# ---- Project root containing the canonical artifact root ----
root=$local_project
[ -z "$root" ] && exit 0
cr=$canonical

# ---- ⚡untracked bypass (per-session flag isolates concurrent sessions) ----
flagbase="$cr/.untracked"; [ -d "$cr" ] || flagbase="$root/.untracked"
[ -n "$sid" ] && flag="$flagbase.$sid" || flag="$flagbase"
[ -f "$flag" ] && exit 0

# ---- Existence helpers ----
has_spec(){ [ -f "$cr/spec/pipeline_state.yaml" ] || ls "$cr"/spec/*/pipeline_state.yaml >/dev/null 2>&1; }
has_research(){ ls -A "$cr/research" >/dev/null 2>&1 || ls -A "$cr/analysis_project" >/dev/null 2>&1; }
block(){ printf '───────────────────────────────────────────\n⛔ %s\n   %s\n───────────────────────────────────────────\n   Bypass: %s → ⚡untracked (this session only)\n' "$1" "$2" "$toggle_label" >&2; exit 2; }

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
