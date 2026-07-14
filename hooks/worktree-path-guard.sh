#!/bin/sh
# worktree-path-guard.sh — enforce the worktree isolation path convention
# from OPERATIONS §5.10 ②.
# PreToolUse(EnterWorktree|Bash) denies only two cases:
#   (a) Built-in EnterWorktree, which creates .claude/worktrees/ inside the
#       repository. The only standard is the sibling path <repo>-wt/<slug>.
#   (b) `git worktree add` whose target is outside the <repo>-wt/ pattern.
# Everything else fails open: the ⚡untracked session flag, canonical sibling
# paths, non-add worktree subcommands, non-git cwd, unknown tools, parse
# failures, and Agent/Workflow worktrees that do not use these tool surfaces.
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

# Unknown tool: fail open.
[ -z "$tool" ] && exit 0

# ---- Project root for display and untracked-flag lookup ----
# Prefer cwd, then the hook process cwd. A non-git location fails open.
if [ -n "$cwd" ]; then
  root=$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null)
else
  root=$(git rev-parse --show-toplevel 2>/dev/null)
fi
[ -z "$root" ] && exit 0

# ---- ⚡untracked bypass (same per-session flag as artifact-guard) ----
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
    deny "Built-in EnterWorktree is forbidden because it creates .claude/worktrees/ inside the repository. Use the sibling-directory standard: git worktree add ${disp_root}-wt/<slug> -b <slug> <base>, register jobs.log, then launch headless work inside that worktree (OPERATIONS §5.10 ②③). Bypass: /track (⚡untracked, this session only)."
    ;;
  Bash)
    # Empty command after parsing: fail open.
    [ -z "$cmd" ] && exit 0
    # Match only `git … worktree add`; ignore non-add subcommands.
    printf '%s' "$cmd" | grep -q 'git' || exit 0
    printf '%s' "$cmd" | grep -Eq 'worktree[[:space:]]+add([[:space:]]|$)' || exit 0
    # Canonical sibling path (<repo>-wt/) is the normal dispatch flow.
    printf '%s' "$cmd" | grep -q -- '-wt/' && exit 0
    deny "The git worktree add target is outside the sibling <repo>-wt/<slug> convention (OPERATIONS §5.10 ②). Use: git worktree add ${disp_root}-wt/<slug> -b <slug> <base>, then register jobs.log. Bypass: /track (⚡untracked, this session only)."
    ;;
  *)
    exit 0
    ;;
esac

exit 0
