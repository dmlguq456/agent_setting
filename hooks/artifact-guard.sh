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
case "$fp" in */_internal/*) exit 0 ;; esac   # Machine-managed snapshot.

# ---- Project root containing the artifact root ----
d=$(dirname "$fp"); root=""
for _ in $(seq 1 40); do
  [ -d "$d/.agent_reports" ] && { root="$d"; break; }
  [ -d "$d/.claude_reports" ] && { root="$d"; break; }
  [ "$d" = "/" ] && break
  d=$(dirname "$d")
done
# Infer the root from an .agent_reports or .claude_reports path even when the
# directory does not yet exist, so the first artifact cannot bypass ordering.
if [ -z "$root" ]; then
  case "$fp" in
    */.agent_reports/*) root="${fp%%/.agent_reports/*}" ;;
    */.claude_reports/*) root="${fp%%/.claude_reports/*}" ;;
  esac
fi
[ -z "$root" ] && exit 0
case "$fp" in
  */.agent_reports/*) cr="$root/.agent_reports" ;;
  */.claude_reports/*) cr="$root/.claude_reports" ;;
  *) [ -d "$root/.agent_reports" ] && cr="$root/.agent_reports" || cr="$root/.claude_reports" ;;
esac

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
