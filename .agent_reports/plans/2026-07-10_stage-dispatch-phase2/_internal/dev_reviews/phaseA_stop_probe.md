# Phase A — SD-14b① probe: does `Stop` hook fire under `claude -p`?

**Date**: 2026-07-10 (execute stage, worktree stage-dispatch-phase2)

## Method (Step A1)
Throwaway `CLAUDE_CONFIG_DIR` with a `Stop` hook appending a sentinel line to a temp file, then a trivial `claude -p "say ok"` turn against it (90s timeout, child-session env stripped).

```
mktemp -d home; settings.json Stop→stop-probe.sh (echo STOP_FIRED >> $STOP_PROBE_OUT)
env -u CLAUDE_CODE_CHILD_SESSION -u AGENT_DISPATCH_DEPTH \
  STOP_PROBE_OUT=$T/fired.log CLAUDE_CONFIG_DIR=$T/home claude -p "say ok"
```

## Result
- `claude -p` exit: **1**
- `$T/fired.log`: **empty / absent** → **STOP DID NOT FIRE**

Verdict: **Stop hook does NOT fire (reliably) under `claude -p`**.

## Runtime-currentness cross-check (Step A2)
WebSearch (Claude Code Stop hook headless), 2026-07:
- Issue #38651 — a `Stop` hook in `-p` corrupts output: the `result` field becomes an empty string (even a `true` no-op reproduces). Other hook types don't.
- Issue #40506 — `PreToolUse` hooks do not fire in `claude -p`.
- Issue #20063 — hooks don't run in headless mode (broad report).

The official-doc / issue landscape is mixed (some say Stop *runs* but empties output; others say hooks don't fire). Our empirical probe is authoritative for the branch (per plan): Stop did not fire here.

**Compound conclusion**: registering a conductor `Stop` gate is not just ineffective — under #38651 it would actively **empty the `-p` result output** of the conductor session, breaking dispatch harvesting. This makes the HOLD decision doubly correct.

## Branch decision (recorded in checklist Decision Points)
- **Stop gate HELD**: Phase E2 creates `hooks/conductor-stop-gate.sh` on disk **UNREGISTERED** (header note + CLI unit test only); it is NOT added to `adapters/claude/settings.json`; no conformance firing test.
- SD-14 still ships via **(a)** wrapper depth-1 `depth_note` one-shot wait clause + **(c)** `utilities/dispatch-wait.sh` polling helper.
- Re-evaluate when Claude Code fixes headless Stop firing (#38651/#20063).

Sources:
- https://github.com/anthropics/claude-code/issues/38651
- https://github.com/anthropics/claude-code/issues/40506
- https://github.com/anthropics/claude-code/issues/20063
- https://code.claude.com/docs/en/headless
