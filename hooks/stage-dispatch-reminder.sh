#!/bin/sh
# PreToolUse(Skill): SD-11 → SD-11b stage-dispatch gate.
#   A depth-1 conductor at standard+ intensity must dispatch each durable stage
#   (code-plan/execute/test/report) as its own depth-2 headless session
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
#     · not conductor_code_stage        → silent (main, depth-2 stage session, non-code)
#     · intensity ∈ {direct,quick}      → silent (these legitimately run inline)
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
#     [--cwd <dir>] [--session <id>] [--depth <n>] [--intensity <i>]
#   Without args, reads Claude PreToolUse hook JSON from stdin.

# 재귀가드: distiller 세션이면 trigger X.
[ "${MEM_DISTILL:-}" = "1" ] && { cat >/dev/null 2>&1; exit 0; }

CODE_STAGES="code-plan code-execute code-test code-report"
HOOK_MODE=1  # 0 = CLI (argv 있음), 1 = stdin hook JSON

is_code_stage() {
  for s in $CODE_STAGES; do [ "$1" = "$s" ] && return 0; done
  return 1
}

# conductor_code_stage — depth-1 conductor 가 code-<stage> 를 in-session 으로 부르는 자리인가.
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
  msg="📌 stage-dispatch: 이 세션은 depth-1 conductor(intensity=${AGENT_DISPATCH_INTENSITY:-?})입니다. ${1} 를 in-session Skill 로 직접 부르는 대신 dispatch-headless.py --depth 2 --parent ${self} --worker-role ${1} 로 스테이지를 분사하고 dispatch-wait 로 수확하세요 (dev-pipeline Step 1~7). in-session Skill 은 direct/quick 또는 headless-불가 런타임 fallback 자리에서만."
  _json_wrap context "$msg"
}

emit_deny() { # $1=skill
  self="${AGENT_DISPATCH_SELF_SLUG:-\$AGENT_DISPATCH_SELF_SLUG}"
  msg="⛔ stage-dispatch deny: depth-1 conductor(intensity=${AGENT_DISPATCH_INTENSITY:-?})가 ${1} 를 in-session Skill 로 직접 호출했습니다. standard+ 에서 스테이지는 반드시 depth-2 headless 로 분사합니다 (dev-pipeline Step 계약). 정규: dispatch-headless.py --depth 2 --parent ${self} --worker-role ${1} 로 분사 → dispatch-wait 로 수확. 정당한 inline 자리(자기수정 사이클 등)면 orchestrator 가 분사 시 STAGE_DISPATCH_INLINE_OK=1 을 명시 부여해야 하며, conductor 재량 예외는 허용되지 않습니다 (§8.6.3)."
  if [ "$HOOK_MODE" -eq 1 ]; then
    _json_wrap deny "$msg"
    exit 0
  fi
  printf '%s\n' "$msg" >&2
  exit 2
}

# decide — 단일 판정 지점. 조건 미충족은 조용히 exit 0.
decide() { # $1=skill $2=depth $3=intensity
  conductor_code_stage "$1" "$2" || return 0
  case "$3" in
    direct|quick) return 0 ;;  # 정당 inline — 조용히.
    standard|strong|thorough|adversarial)
      if [ "${STAGE_DISPATCH_INLINE_OK:-}" = "1" ]; then
        emit_reminder "$1"     # orchestrator 명시 opt-out → soft reminder.
      else
        emit_deny "$1"         # hard deny.
      fi
      ;;
    *)  # intensity 불명(구 wrapper) — 하위호환: reminder 만, deny 금지(false-positive 방지).
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
      --depth) depth=$2; shift 2 ;;
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
