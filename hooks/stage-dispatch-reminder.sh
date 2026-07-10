#!/bin/sh
# PreToolUse(Skill): SD-11 stage-dispatch reminder (soft / non-deny).
#   A depth-1 conductor at standard+ intensity should dispatch each durable
#   stage (code-plan/execute/test/report) as its own depth-2 headless session
#   (dev-pipeline Step 1~7), not invoke code-<stage> in-session. When it is
#   about to call code-<stage> as an in-session Skill, emit an additionalContext
#   reminder — NOT a deny. The hook cannot deterministically tell a legitimate
#   headless-unavailable fallback from a mistake, so a deny would false-positive
#   (§8.5.2, §14-(4)); deny escalation is deferred pending drill/instrumentation.
#
#   Fire only when ALL hold (else clean exit 0):
#     - CLAUDE_CODE_CHILD_SESSION=1 and AGENT_DISPATCH_DEPTH=1 (a conductor,
#       not main, not a depth-2 stage session)
#     - AGENT_DISPATCH_INTENSITY in {standard,strong,thorough,adversarial}
#       (direct/quick legitimately run inline — this is why reminder, not deny)
#     - the invoked skill in {code-plan,code-execute,code-test,code-report}
#   Recursion guard: MEM_DISTILL=1 → drain stdin, exit 0 (mirror memory hooks).
#
#   Portable CLI (conformance): stage-dispatch-reminder.sh --skill <name>
#     [--cwd <dir>] [--session <id>] [--depth <n>] [--intensity <i>]
#   Without args, reads Claude PreToolUse hook JSON from stdin.
#   Read-only: emits context only, never blocks, never writes.

# 재귀가드: distiller 세션이면 trigger X.
[ "${MEM_DISTILL:-}" = "1" ] && { cat >/dev/null 2>&1; exit 0; }

CODE_STAGES="code-plan code-execute code-test code-report"

is_code_stage() {
  for s in $CODE_STAGES; do [ "$1" = "$s" ] && return 0; done
  return 1
}

fires() { # $1=skill $2=depth $3=intensity ; env: CLAUDE_CODE_CHILD_SESSION
  skill=$1; depth=$2; intensity=$3
  [ "${CLAUDE_CODE_CHILD_SESSION:-}" = "1" ] || return 1
  [ "$depth" = "1" ] || return 1
  case "$intensity" in
    standard|strong|thorough|adversarial) ;;
    *) return 1 ;;
  esac
  is_code_stage "$skill" || return 1
  return 0
}

emit_context() { # $1=skill
  self="${AGENT_DISPATCH_SELF_SLUG:-\$AGENT_DISPATCH_SELF_SLUG}"
  msg="📌 stage-dispatch: 이 세션은 depth-1 conductor(intensity=${AGENT_DISPATCH_INTENSITY:-?})입니다. ${1} 를 in-session Skill 로 직접 부르는 대신 dispatch-headless.py --depth 2 --parent ${self} --worker-role ${1} 로 스테이지를 분사하고 dispatch-wait 로 수확하세요 (dev-pipeline Step 1~7). in-session Skill 은 direct/quick 또는 headless-불가 런타임 fallback 자리에서만."
  # JSON escape via python (safe for quotes/unicode).
  printf '%s' "$msg" | python3 -c 'import sys,json; print(json.dumps({"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":sys.stdin.read()}}, ensure_ascii=False))'
}

# --- CLI mode ---
if [ "$#" -gt 0 ]; then
  skill=""; depth="${AGENT_DISPATCH_DEPTH:-}"; intensity="${AGENT_DISPATCH_INTENSITY:-}"
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --skill) skill=$2; shift 2 ;;
      --cwd) shift 2 ;;
      --session) shift 2 ;;
      --depth) depth=$2; shift 2 ;;
      --intensity) intensity=$2; shift 2 ;;
      -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
      *) echo "stage-dispatch-reminder: unknown arg '$1'" >&2; exit 64 ;;
    esac
  done
  [ -n "$skill" ] || { echo "stage-dispatch-reminder: --skill required" >&2; exit 64; }
  AGENT_DISPATCH_INTENSITY="$intensity"
  if fires "$skill" "$depth" "$intensity"; then emit_context "$skill"; fi
  exit 0
fi

# --- stdin (Claude hook JSON) mode ---
input=$(cat 2>/dev/null)
[ -z "$input" ] && exit 0
skill=$(printf '%s' "$input" | grep -o '"skill"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"skill"[[:space:]]*:[[:space:]]*"//; s/"$//')
if fires "$skill" "${AGENT_DISPATCH_DEPTH:-}" "${AGENT_DISPATCH_INTENSITY:-}"; then emit_context "$skill"; fi
exit 0
