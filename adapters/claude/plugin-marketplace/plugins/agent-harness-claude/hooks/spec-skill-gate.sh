#!/bin/sh
# PreToolUse(Skill): spec 청사진을 _변경_ 하는 skill(autopilot-code/spec)을 spec-backed cwd에서
# 호출할 때, 이번 세션에 prd.md를 '실제 Read'(마커 존재)하지 않았으면 DENY.
# Portable CLI: spec-skill-gate.sh --skill <name> [--cwd <dir>] [--session <id>] [--agent-home <dir>]
# prd.md가 Read 이후 갱신됐으면(역방향 drift)도 DENY → 재Read 강제.
# self-report가 아니라 검증 가능한 하드 게이트. POSIX sh, no jq.
# (autopilot-note 제외 — digest skill 이라 spec 청사진을 안 바꿈. 2026-06-16 audit #16.)

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
AGENT_HOME="${AGENT_HOME:-$("$SCRIPT_DIR/../utilities/agent-home.sh")}"

usage() {
  cat <<'EOF'
usage: spec-skill-gate.sh --skill <name> [--cwd <dir>] [--session <id>] [--agent-home <dir>]
       spec-skill-gate.sh --capability <name> [--cwd <dir>] [--session <id>] [--agent-home <dir>]

Without arguments, reads Claude hook JSON from stdin.
EOF
}

find_prd() {
  dir=$1
  prd=""
  root=""
  for _ in 0 1 2 3; do
    if [ -f "$dir/.agent_reports/spec/prd.md" ]; then prd="$dir/.agent_reports/spec/prd.md"; root="$dir"; break; fi
    if [ -f "$dir/.claude_reports/spec/prd.md" ]; then prd="$dir/.claude_reports/spec/prd.md"; root="$dir"; break; fi
    parent=$(dirname "$dir")
    [ "$parent" = "$dir" ] && break
    dir=$parent
  done
}

check_gate() {
  skill=$1
  cwd=$2
  sid=$3

  case "$skill" in
    autopilot-code|autopilot-spec) ;;
    *) return 0 ;;   # spec-governed 아닌 capability → 통과
  esac

  find_prd "$cwd"
  [ -z "$prd" ] && return 0   # spec-backed 아님 → 통과

  key=$(printf '%s' "$root" | sed 's#[/ ]#_#g')
  marker="$AGENT_HOME/.spec-grounding/${sid}__${key}"
  cur=$(stat -c %Y "$prd" 2>/dev/null || echo 0)

  if [ ! -f "$marker" ]; then
    reason="spec-backed cwd인데 prd.md를 이번 세션에 Read하지 않음. $prd 를 Read 도구로 직접 읽은 뒤 다시 호출하세요. 코드 주석·brief 인용은 무효 — 실제 Read만 게이트를 통과합니다."
    return 2
  fi

  read_mtime=$(cat "$marker" 2>/dev/null || echo 0)
  if [ "$cur" -gt "$read_mtime" ]; then
    reason="prd.md가 마지막 Read 이후 갱신됨(역방향 drift). $prd 를 다시 Read한 뒤 호출하세요."
    return 2
  fi

  return 0
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
