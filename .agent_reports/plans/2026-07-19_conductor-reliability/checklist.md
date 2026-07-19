# Verification Checklist — conductor reliability

Intensity `strong` → verification rigor maps to standard/thorough (CONVENTIONS §1.1). Run from the worktree `/home/Uihyeop/agent_setting-wt/conductor-reliability`. `.test.py` suites are stdlib `unittest` scripts run directly with `python3 <file>`. Delete test-created `__pycache__` before each commit.

## Per-commit gates (run before committing each group)

### Always (every commit)
- [ ] `git diff --check` clean (no whitespace/conflict markers).
- [ ] `python3 -m py_compile` on every touched `.py`; `bash -n` on every touched `.sh`.
- [ ] `find . -name __pycache__ -type d -not -path '*/.dispatch/*' -prune -exec rm -rf {} +` before commit.

### C1 — core contract (`core/OPERATIONS.md`)
- [x] `bash tools/check-adaptation-boundary.sh` (core↔adapter boundary intact). — OK, pre-existing WARN unrelated.
- [x] `bash hooks/core-first-guard.sh` path exercised / core read before adapter edits. — core/OPERATIONS.md read+committed (9d580b8e) before any adapter edit.
- [x] No `spec/**` diff; no `utilities/dispatch-route.sh` diff. — confirmed via `git status`.

### C2 — SD-70 completion marker ↔ exact attempt row
- [x] `python3 utilities/dispatch_completion_marker.test.py` — 8 tests OK
- [x] `python3 utilities/capability_route.test.py` — 11 tests OK
- [x] `python3 utilities/dispatch_contract.test.py` (close_attempt_row idempotency regression) — 10 tests OK
- [x] `python3 utilities/dispatch_registry.test.py` (marker-backed reconcile repair) — 13 tests OK
- [x] New cases proven: prior-BLOCKED/current-PASS/live-retry → only current closed; duplicate complete; mismatch/missing attempt fail-closed marker-preserved; unwritable jobs → marker preserved + reconcile repair; never breadth-close. (commit de7db348)

### C3 — SD-64/71 orphan reconcile + visibility
- [x] `python3 utilities/dispatch_registry.test.py` (orphan fixture: dead owner + open child → `dead-parent-orphaned`; live conductor/completed route/live child → zero false positive; un-started successor variant; live child never closed). — classify-layer landed in de7db348; surfaces below still pending.
- [x] `python3 utilities/dispatch_node.test.py` (route/node metadata regression). — 17 tests OK
- [x] `bash utilities/dispatch-liveness.sh <fixture jobs.log>` shows `⚠️ ORPHANED` with resume boundary; exit 3 preserved. — verified manually + adapters/codex/bin/dispatch-liveness.py equivalent
- [x] `adapters/codex/bin/preflight.sh status` emits `orphaned_conductor_jobs` (+ `orphaned_resume_boundary` when >0); fail-open 0 with no registry. — verified against real registry (0) + fixture (1, resume_boundary set)
- [x] `python3 tools/fleet/tests/test_f26_registry.py` and `python3 tools/fleet/tests/test_f28_route.py` (current-attempt view surfaces `dead-parent-orphaned`, never blank cell). — 41 + 23 tests OK (commit 225eefc6)

### C4 — SD-69 Codex linked-worktree mutation boundary
- [x] `python3 adapters/codex/bin/dispatch-headless.sd45.test.py` (argv/sandbox regression). — 9 tests OK
- [x] New disposable linked-worktree fixture: writable roots include primary `.spec-grounding` + artifact root, exclude git-common-dir/`.git`; source edit persists; `.spec-grounding/<marker>` lands in **primary** checkout; `no_commit=1` recorded, no commit claimed, `route_hash`/`source_commit` unforged. — `utilities/dispatch_codex_nocommit_fixture.test.py`, 2 tests OK
- [x] `python3 utilities/worker_route_guard.test.py` (no regression; no-commit stage `HEAD==source_commit` still passes; SD-67 first-parent retry lineage intact). — 13 tests OK, no change needed (guard doesn't read the pipe)
- [x] `python3 utilities/dispatch_node.test.py` (no_commit metadata forwarded). — 17 tests OK; no_commit is self-detected inside dispatch-headless.py from args it already receives (route_node/write_scope/worktree/agent_home), so no new dispatch-node.py passthrough flag was needed — same observable outcome (registry row carries `no_commit=1`), documented in dev_logs.
- [x] Throwaway repo + `__pycache__` removed after fixture. — tearDown() removes the linked worktree; TemporaryDirectory cleans the rest

### C5 — SD-71 Claude one-shot conductor hardening
- [x] Runtime probe evidence captured: `_internal/probe_claude_tools.txt` (tool-policy enumeration, live `claude -p` 2.1.215) and `_internal/probe_stop_hook.txt` (Stop fire/block/stdout, 9/9 fires but empty stdout both runs). Denied names ⊆ probe-proven async tools (Monitor, ScheduleWakeup, CronCreate, CronDelete, CronList, PushNotification, RemoteTrigger); `Bash` never denied.
- [x] Stop gate registered ONLY if fire+block+stdout all hold; else held fallback retained (documented). — stdout was empty both probe runs → gate stays disabled, existing core/OPERATIONS.md §5.10 held-fallback text confirmed unchanged.
- [x] `python3 adapters/claude/bin/dispatch-headless.sd45.test.py` + new deny/fallback cases: owner gets exactly the proven `--disallowedTools` names, never `Bash`; stage worker gets none; empty proven list → no flag. — 15 tests OK (commit e44c77a2)
- [x] Prompt contract: owner prompt carries the standard synchronous-wait / no-async clause (auxiliary layer only). — both Claude and Codex wrappers, 12+15 tests OK

## Whole-cycle floor (test worker verifies the committed worktree, not execute logs)
- [x] Affected existing suites green: `dispatch_contract`(10), `dispatch_registry`(13), `dispatch_node`(17), `capability_route`(11), `dispatch_completion_marker`(8), `worker_route_guard`(13), `stage_dispatch_fallback`(8), `nested_dispatch_eligibility`(4) (`.test.py`), plus fleet `test_f25_state_model.py`(33), `test_f26_registry.py`(41), `test_f28_route.py`(23), `test_dispatch.py`(73).
- [x] `bash tools/check-adaptation-boundary.sh` green. — pre-existing WARN (103 concrete refs) unrelated.
- [ ] Portable guard suite at strong assurance: `bash hooks/portable-guards.test.sh` — PASS=366 FAIL=2; identifying + confirming the 2 failures are pre-existing (unrelated to this cycle) before closing this line.
- [x] `git diff --check` clean repo-wide; no `__pycache__` staged; `spec/**` and `utilities/dispatch-route.sh` untouched; unrelated dirty/untracked state preserved. — verified via `git diff b9364824..HEAD --stat -- spec/ utilities/dispatch-route.sh` (both empty) and `git status --short` (clean).
- [x] Parity honesty disclosed: Claude-only `--disallowedTools`, Codex-only `.spec-grounding`/no-commit — asymmetry recorded in wrapper comments + dev_logs/execute-r2.md.
