#!/bin/sh
# worktree-path-guard.sh — 본작업 worktree 격리 경로 컨벤션 hard 강제 (OPERATIONS §5.10 ②).
# PreToolUse(EnterWorktree|Bash) 2갈래 deny:
#   (a) 내장 EnterWorktree 전면 deny — repo 안 .claude/worktrees/ 에 worktree 를 파 main
#       워킹트리를 미추적 .claude/ 로 오염한다 (drill g3/g6). 형제 디렉토리 <repo>-wt/<slug> 가 유일 표준.
#   (b) Bash `git worktree add` 인데 대상 경로가 <repo>-wt/ 패턴 밖이면 deny (동일 안내).
# 오차단 금지 (fail-open 이 기본, 막는 건 위 2갈래뿐):
#   · ⚡untracked 세션 flag(artifact-guard 와 동일 <artifact-root>/.untracked.<sid>) 존재 → 통과
#   · 정규 경로 <repo>-wt/<slug> 의 `git worktree add` → 통과 (오케스트레이터·conductor 분사 흐름)
#   · `git worktree remove|list|prune|move|lock…` 등 비-add 서브커맨드 → 무간섭
#   · 비-git cwd / tool 미상 / 입력 파싱 실패 → 통과 (가드 오작동으로 전 세션 마비 방지, git-state-guard 선례)
#   · Agent(isolation:worktree)·Workflow worktree 는 Bash/EnterWorktree 툴이 아니라 애초에 미매칭 → 무영향.
# builtin-memory-guard 동형: 내장 하네스 표면이 컨벤션과 다른 기본값을 제공 → PreToolUse deny + 정규 경로 안내.
# POSIX sh, no jq. Dual mode: hook(stdin JSON) + CLI(--tool/--command/--cwd/--session).

tool=""
cmd=""
cwd=""
sid=""
hook_mode=1

if [ "$#" -gt 0 ]; then
  hook_mode=0
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --tool)    [ "$#" -ge 2 ] || { echo "worktree-path-guard: --tool requires a value" >&2; exit 64; }; tool="$2"; shift 2 ;;
      --command) [ "$#" -ge 2 ] || { echo "worktree-path-guard: --command requires a value" >&2; exit 64; }; cmd="$2"; shift 2 ;;
      --cwd)     [ "$#" -ge 2 ] || { echo "worktree-path-guard: --cwd requires a path" >&2; exit 64; }; cwd="$2"; shift 2 ;;
      --session) [ "$#" -ge 2 ] || { echo "worktree-path-guard: --session requires an id" >&2; exit 64; }; sid="$2"; shift 2 ;;
      --help|-h) echo "usage: worktree-path-guard.sh --tool <EnterWorktree|Bash> [--command <cmd>] [--cwd <dir>] [--session <id>]"; exit 0 ;;
      *) echo "worktree-path-guard: unknown argument: $1" >&2; exit 64 ;;
    esac
  done
else
  input=$(cat 2>/dev/null)
  [ -z "$input" ] && exit 0
  tool=$(printf '%s' "$input" | grep -o '"tool_name"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"tool_name"[[:space:]]*:[[:space:]]*"//; s/"$//')
  cwd=$(printf '%s' "$input" | grep -o '"cwd"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"cwd"[[:space:]]*:[[:space:]]*"//; s/"$//')
  sid=$(printf '%s' "$input" | grep -o '"session_id"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"session_id"[[:space:]]*:[[:space:]]*"//; s/"$//')
  cmd=$(printf '%s' "$input" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"command"[[:space:]]*:[[:space:]]*"//; s/"$//')
fi

# tool 미상 → fail-open.
[ -z "$tool" ] && exit 0

# ---- 프로젝트 루트 (표시용 + untracked flag 조회) ----
# cwd 우선, 없으면 hook 프로세스 cwd. 둘 다 비-git 이면 무간섭 (fail-open) — worktree 는 git repo 에서만
# 의미 있으므로 non-git 에서 deny 하면 순수 오차단.
if [ -n "$cwd" ]; then
  root=$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null)
else
  root=$(git rev-parse --show-toplevel 2>/dev/null)
fi
[ -z "$root" ] && exit 0

# ---- ⚡untracked 우회 (artifact-guard 와 동일 세션별 flag) ----
if [ -n "$sid" ]; then
  for base in "$root/.agent_reports/.untracked" "$root/.claude_reports/.untracked" "$root/.untracked"; do
    [ -f "$base.$sid" ] && exit 0
  done
fi

disp_root="$root"

deny() {
  reason=$1
  if [ "$hook_mode" -eq 1 ]; then
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$reason"
    exit 0
  fi
  printf '⛔ %s\n' "$reason" >&2
  exit 2
}

case "$tool" in
  EnterWorktree)
    deny "내장 EnterWorktree 금지 — repo 안 .claude/worktrees/ 에 worktree 를 파 main 워킹트리를 미추적 .claude/ 로 오염한다 (drill g3/g6). 형제 디렉토리 단일 표준: git worktree add ${disp_root}-wt/<slug> -b <slug> <base> → jobs.log 등록 → 그 worktree 안에서 headless(claude -p) 분사 (OPERATIONS §5.10 ②③). 우회: /track (⚡untracked, 이 세션만)."
    ;;
  Bash)
    # 파싱 실패로 command 가 비면 fail-open.
    [ -z "$cmd" ] && exit 0
    # `git … worktree add` 만 대상 — remove/list/prune/move/lock 등 비-add 서브커맨드는 무간섭.
    printf '%s' "$cmd" | grep -q 'git' || exit 0
    printf '%s' "$cmd" | grep -Eq 'worktree[[:space:]]+add([[:space:]]|$)' || exit 0
    # 정규 형제 경로(<repo>-wt/) 를 가리키면 통과 — 오케스트레이터·conductor 의 정상 분사 흐름.
    printf '%s' "$cmd" | grep -q -- '-wt/' && exit 0
    deny "git worktree add 경로가 형제 디렉토리 <repo>-wt/<slug> 컨벤션 밖 (OPERATIONS §5.10 ②, -wt/ 단일 표준·변형 금지). 정규: git worktree add ${disp_root}-wt/<slug> -b <slug> <base> → jobs.log 등록. 우회: /track (⚡untracked, 이 세션만)."
    ;;
  *)
    exit 0
    ;;
esac

exit 0
