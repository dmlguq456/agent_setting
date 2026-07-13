# Verification Report

**Target**: `.agent_reports/plans/2026-07-13_token-self-regulation/plan.md` and all changed source/docs/tests
**Mode**: `qa/test`, verification-runner tool contract satisfied
**Intensity**: thorough

## Level 1 — Syntax

- PASS: AST parse of all changed Python modules, collectors, tests, CLI, and Codex hook.
- Command: `preflight.sh verification-runner --timeout 60 -- python3 -c <ast parse> <changed py files>`
- Exit: 0.

## Level 2 — Import

- PASS: focused unittest imported `fleet.token_budget`, all three collectors, `Session`, and executed the CLI as a subprocess.
- Covered by the focused and full Fleet suites below.

## Level 3 — Smoke

- PASS: 12 focused tests.
- Command: `python3 -m unittest -v tools.fleet.tests.test_token_budget`
- Evidence: formula boundaries; last-vs-total parsing; malformed/missing/stale/ambiguous lookup; event timestamp before fresh file mtime; Codex/Claude/OpenCode field mapping; transition-only state; persisted/manual decreasing-counter fail-open; unwritable-state fail-open; concurrent single emission; directive byte cap.

## Level 4 — Functional

- PASS: 202 Fleet tests.
- Command: `python3 -m unittest discover -s tools/fleet/tests -p test_*.py`
- PASS: portable hook/guard integration suite.
- Command: `bash hooks/portable-guards.test.sh`
- Result: `PASS=343 FAIL=0`.
- Evidence: exact-session `preflight token-budget` exposed active/cumulative fields; first tight transition injected one compact line; repeated band produced zero hook output; existing hook/dispatch/memory/guard contracts remained green.

## Level 5 — Integration/contracts

- PASS: `bash tools/check-adaptation-boundary.sh` after one correction round.
  - Initial failure: new utility lacked adapter projection classification and Claude utility mirror.
  - Fix: Claude + Codex selective projections, OpenCode deferred decision, core inventory entry.
  - Final: `OK: adaptation boundary checks passed` (existing informational 56-reference warning only).
- PASS: manifest and all Codex native skill/plugin/agent/mode checks.
- PASS: `git diff --check`.
- PASS: repository `preflight.sh doctor`, including new `check=token-budget:ok`.
- PASS: canonical/Claude parser and focused-test mirrors are byte-identical.

## Independent review correction round

- Counter decrease was initially only observable with explicit `--previous-session-total-tokens`; normal baselines are now persisted and both hook plus `kv`/`json` detect a decrease.
- Staleness initially used rollout file mtime; current token-count event timestamps now take precedence, with mtime retained only for legacy rows.
- UserPromptSubmit initially had no token-budget-specific bound; it now has an independent fail-open timeout and process-group termination.
- The transition lock initially imported POSIX-only `fcntl`; it now uses a bounded atomic directory lock.
- The first AST verification-runner invocation had an argument-quoting error. The command was corrected and the same changed-file AST set passed with exit 0; this was a test invocation issue, not a source failure.

## Level 5b — Behavioral runtime observation

- PASS through the installed-fixture Codex lifecycle in `portable-guards.test.sh`: runtime-shaped UserPromptSubmit JSON -> exact rollout lookup -> transition directive -> repeated-band silence.
- No live `$CODEX_HOME` config or transcript was modified.

## Runtime projection note

- `doctor --runtime`: FAIL because the installed `$CODEX_HOME` projection points to the main checkout rather than this feature worktree, and its `hooks.json` is not the worktree projection. This was the pre-existing reason headless dispatch was unavailable and is expected before branch integration/reinstall; repository readiness doctor is green.
- Hook trust itself reports ok. No runtime projection mutation was attempted from the worktree.

Post-integration update: main was fast-forwarded and the installed projection was
refreshed with `--skills-mode native`. The strict
`runtime-projection --require-hook-trust` check passes with
`hooks-json:ok` and hook trust ok.

## Verdict

PASS for repository implementation, adapter contracts, and the post-integration
installed-runtime projection.
