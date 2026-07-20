#!/bin/sh
# PreToolUse(Skill): SD-11 → SD-11b stage-dispatch gate.
#   A dispatch-depth-1 conductor at standard+ intensity must dispatch each durable stage
#   (code-plan/execute/test/report) as its own dispatch-depth-2 headless session
#   (dev-pipeline Step 1~7), not invoke code-<stage> in-session.
#
#   SD-11 shipped this as a *soft reminder* because the hook could not tell a
#   legitimate inline fallback from a mistake. SD-11b (§8.6.3) closes that gap:
#   the wrapper now injects AGENT_DISPATCH_INTENSITY into every child env
#   (dispatch-headless.py, all 3 adapters), so [conductor + standard+ + code-<stage>]
#   is a *deterministic* condition. The soft reminder failed twice in a row
#   (a minimal-prompt conductor borrowed a self-modification exception and ran
#   inline anyway), so at that deterministic condition we now **hard deny**.
#
#   Decision (else clean exit 0 / silent):
#     conductor_code_stage = CLAUDE_CODE_CHILD_SESSION=1 AND AGENT_DISPATCH_DEPTH=1
#                            AND skill ∈ {code-plan,code-execute,code-test,code-report}
#     · not conductor_code_stage        → silent (main, dispatch-depth-2 stage session, non-code)
#     · intensity ∈ {direct,quick}      → silent (direct inline; quick is a dispatch-depth-1 one-shot worker)
#     · intensity ∈ {standard,strong,thorough,adversarial}:
#         · STAGE_DISPATCH_INLINE_OK=1   → soft reminder (orchestrator granted an explicit
#                                          inline opt-out — e.g. a self-modification cycle
#                                          editing the dispatch launch path itself, §8.6.3(c))
#         · else                         → HARD DENY + dispatch-headless guidance
#     · intensity unknown/empty          → soft reminder (old wrapper without the env; cannot
#                                          confirm standard+, so never deny — no false positive)
#   Recursion guard: MEM_DISTILL=1 → drain stdin, exit 0 (mirror memory hooks).
#
#   Deny mechanism mirrors worktree-path-guard.sh (drill g3/g6 precedent):
#     hook(stdin) mode → JSON permissionDecision=deny, exit 0
#     CLI mode         → "⛔ ..." on stderr, exit 2
#
#   Portable CLI (conformance): stage-dispatch-reminder.sh --skill <name>
#     [--cwd <dir>] [--session <id>] [--dispatch-depth <n>] [--intensity <i>]
#   Without args, reads Claude PreToolUse hook JSON from stdin.

# Recursion guard: never trigger in a distiller session.
[ "${MEM_DISTILL:-}" = "1" ] && { cat >/dev/null 2>&1; exit 0; }

CODE_STAGES="code-plan code-execute code-test code-report"
HOOK_MODE=1  # 0 = CLI (argv present), 1 = stdin hook JSON

is_code_stage() {
  for s in $CODE_STAGES; do [ "$1" = "$s" ] && return 0; done
  return 1
}

# conductor_code_stage — whether a dispatch-depth-1 conductor invokes code-<stage> in-session.
conductor_code_stage() { # $1=skill $2=depth ; env: CLAUDE_CODE_CHILD_SESSION
  [ "${CLAUDE_CODE_CHILD_SESSION:-}" = "1" ] || return 1
  [ "$2" = "1" ] || return 1
  is_code_stage "$1" || return 1
  return 0
}

_json_wrap() { # $1=json-field-name $2=message ; emit PreToolUse hookSpecificOutput
  printf '%s' "$2" | python3 -c 'import sys,json
field=sys.argv[1]; msg=sys.stdin.read()
out={"hookSpecificOutput":{"hookEventName":"PreToolUse"}}
if field=="deny":
    out["hookSpecificOutput"]["permissionDecision"]="deny"
    out["hookSpecificOutput"]["permissionDecisionReason"]=msg
else:
    out["hookSpecificOutput"]["additionalContext"]=msg
print(json.dumps(out, ensure_ascii=False))' "$1"
}

emit_reminder() { # $1=skill
  self="${AGENT_DISPATCH_SELF_SLUG:-\$AGENT_DISPATCH_SELF_SLUG}"
  node=${1#code-}
  msg="📌 stage-dispatch: this session is a dispatch-depth-1 conductor (intensity=${AGENT_DISPATCH_INTENSITY:-?}). Dispatch ${1} route-bound with dispatch-node.py --route <route-file> --node ${node} --adapter <adapter> --action start --slug <stage-slug> --parent ${self} -- --jobs <canonical-jobs.log>; capture the emitted attempt_id, harvest with dispatch-wait, then complete that exact route/node/attempt (dev-pipeline steps 1-7). Invoke the Skill in-session only for direct inline work, a quick one-shot worker, or a runtime fallback where registered headless dispatch is unavailable."
  _json_wrap context "$msg"
}

emit_deny() { # $1=skill
  self="${AGENT_DISPATCH_SELF_SLUG:-\$AGENT_DISPATCH_SELF_SLUG}"
  node=${1#code-}
  msg="⛔ stage-dispatch denied: a dispatch-depth-1 conductor (intensity=${AGENT_DISPATCH_INTENSITY:-?}) invoked ${1} in-session. At standard+ intensity, use dispatch-node.py --route <route-file> --node ${node} --adapter <adapter> --action start --slug <stage-slug> --parent ${self} -- --jobs <canonical-jobs.log>; capture attempt_id, harvest with dispatch-wait, and complete that exact route/node/attempt. A legitimate inline case such as a self-modification cycle requires the orchestrator to set STAGE_DISPATCH_INLINE_OK=1 when launching; the conductor cannot grant itself an exception (§8.6.3)."
  if [ "$HOOK_MODE" -eq 1 ]; then
    _json_wrap deny "$msg"
    exit 0
  fi
  printf '%s\n' "$msg" >&2
  exit 2
}

# decide — single decision point; unmet conditions exit silently with status 0.
decide() { # $1=skill $2=depth $3=intensity
  conductor_code_stage "$1" "$2" || return 0
  case "$3" in
    direct|quick) return 0 ;;  # Direct inline / quick one-shot worker: stay silent.
    standard|strong|thorough|adversarial)
      if [ "${STAGE_DISPATCH_INLINE_OK:-}" = "1" ]; then
        emit_reminder "$1"     # Explicit orchestrator opt-out: soft reminder.
      else
        emit_deny "$1"         # hard deny.
      fi
      ;;
    *)  # Unknown intensity from an older wrapper: reminder only to avoid false-positive denial.
      emit_reminder "$1"
      ;;
  esac
}

# --- CLI mode ---
if [ "$#" -gt 0 ]; then
  HOOK_MODE=0
  skill=""; depth="${AGENT_DISPATCH_DEPTH:-}"; intensity="${AGENT_DISPATCH_INTENSITY:-}"
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --skill) skill=$2; shift 2 ;;
      --cwd) shift 2 ;;
      --session) shift 2 ;;
      --dispatch-depth) depth=$2; shift 2 ;;
      --intensity) intensity=$2; shift 2 ;;
      -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
      *) echo "stage-dispatch-reminder: unknown arg '$1'" >&2; exit 64 ;;
    esac
  done
  [ -n "$skill" ] || { echo "stage-dispatch-reminder: --skill required" >&2; exit 64; }
  AGENT_DISPATCH_INTENSITY="$intensity"
  decide "$skill" "$depth" "$intensity"
  exit 0
fi

# --- stdin (Claude hook JSON) mode ---
input=$(cat 2>/dev/null)
[ -z "$input" ] && exit 0
skill=$(printf '%s' "$input" | grep -o '"skill"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"skill"[[:space:]]*:[[:space:]]*"//; s/"$//')
decide "$skill" "${AGENT_DISPATCH_DEPTH:-}" "${AGENT_DISPATCH_INTENSITY:-}"
exit 0
