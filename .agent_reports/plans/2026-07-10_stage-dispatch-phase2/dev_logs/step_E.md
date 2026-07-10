# dev_log — Phase E (hooks: SD-11 reminder + SD-14b Stop gate)

## E1 — hooks/stage-dispatch-reminder.sh (SD-11, soft / non-deny) — REGISTERED
- PreToolUse(Skill) hook. Fires only when conductor (`CLAUDE_CODE_CHILD_SESSION=1` + `AGENT_DISPATCH_DEPTH=1`) at intensity∈{standard,strong,thorough,adversarial} is about to invoke a code-{plan,execute,test,report} Skill → emits `additionalContext` reminder (NOT deny). Recursion guard MEM_DISTILL=1. CLI: `--skill/--cwd/--session/--depth/--intensity`.
- **Registered** in `adapters/claude/settings.json` PreToolUse as a 2nd `Skill` matcher (co-exists with spec-skill-gate). settings.json validates (json.tool).
- Conformance (portable-guards.test.sh): (i) conductor+standard+code-plan → emits additionalContext; (ii) quick → no-op; (iii) depth-2 → no-op; (iv) non-code skill → no-op; (v) main → no-op. **All 5 PASS.**

## E2 — hooks/conductor-stop-gate.sh (SD-14b) — UNREGISTERED / HELD
- Per Phase A verdict: `claude -p` does not fire Stop + CC #38651 (Stop empties `-p` output). Script created on disk with a header HOLD note + full logic + CLI (`--self-slug/--jobs/--stop-active`), but **NOT added to settings.json**. Blocks conductor turn-end while open `parent=<self-slug>` children exist (ALIVE→poll; SUSPECT/DEAD→diagnose); loop guard on stop_hook_active.
- CLI unit cases in portable-guards.test.sh: no children→no block; dead child→block-diagnose; stop_hook_active→no block; non-conductor env→no block. **All 4 PASS.**

## E3 — core/HOOKS.md Invariant Catalog
- Added two rows: `stage-dispatch reminder` (portable-check, soft/fail-open) and `conductor Stop gate` (portable-check, marked UNREGISTERED — conditional on headless Stop firing). Parity note for codex/opencode AGENTS.md deferred to Phase G (one-shot clause).

## Regression note (important for code-test)
- `hooks/portable-guards.test.sh`: my 9 new E1/E2 cases all PASS. The suite reports ~12 pre-existing environmental FAILs (codex/opencode dispatch wrappers, codex doctor, dispatch-liveness transcript ALIVE/SUSPECT timing, "claude dispatch wrapper cross-harness metadata"). **Confirmed pre-existing**: running the suite from baseline commit `8596e25` (before any Phase-2 edit) reproduces the same failures (claude-wrapper + all 4 dispatch-liveness cases fail identically). These are environment-sensitive (codex/opencode CLIs absent, transcript mtime, git fixture) — **not introduced by this plan**. Standalone `dispatch-wait.test.sh` and `dispatch-liveness.test.sh` both PASS.
