# Fast independent plan check 2

verdict: **FAIL**

scope: verification feasibility, Fleet mirror parity, direct-headless constraints, and artifact/commit gates for `plan.md`.

## Required corrections

1. **Assign the live direct-headless `--start` smoke to the depth-1 owner.** The plan places all verification in one sequence without saying which stage owns step 10. A registered `code-test` worker is depth 2; allowing it to start a real nested stage would create forbidden depth 3. Make the split explicit: depth-2 `code-test` may run hermetic fake-CLI/fixture coverage, while the depth-1 owner performs and polls any real same-harness/cross-harness direct-headless start after harvesting the test worker. The owner must retain current-turn polling, close registry rows, and record the smoke evidence.

2. **Make the post-verification commit and artifact gates owner-owned and ordered.** State explicitly that the depth-1 owner, not a depth-2 stage worker, performs the final source commit only after all focused/full tests, parity, portable guards, syntax/compile, adaptation boundary, and owner-only live smoke pass. Then require the owner to record the commit id in canonical development and final artifacts and verify the source worktree is clean except for any explicitly documented pre-existing state. This removes ambiguity around the `code-test -> code-report` transition and keeps commit authority out of nested workers.

3. **Name the complete canonical artifact set in the completion gate.** The assignment requires durable plan/checklist/dev/test/final artifacts. The cycle already contains `plan.md` and `checklist.md`, but the plan's completion gate names only dev/test/final generically. Add exact canonical targets (or an unambiguous naming contract) for checklist updates, development log, test report/logs, and final report, and require each to include command, result, warnings, and commit/no-push state. Do not put these durable artifacts in the worktree shadow.

## Confirmed strengths

- SD-58, SD-59, and SD-60 are ordered correctly, and SD-58 provides the single F-25 evidence source consumed by watchdog and reconciliation.
- Speech-only activity is excluded, exact PID/start revalidation precedes interrupt, native-subagent proof fails closed, and fallback remains the checked direct chain.
- Capacity selection remains in the route/orchestrator layer; wrappers only classify and close `dead-capacity`; the tests cover one different retry and same-model count zero.
- SD-60 reuses SD-29 safety gates and SD-49 identity under lock, with dry-run/idempotency/current-filter coverage.
- Canonical `tools/fleet/` and `adapters/claude/tools/fleet/` byte parity is explicitly required, including fixtures/tests, and wrapper parity is tested separately.
- The sequential verification order is feasible and correctly keeps test-created `__pycache__` away from adaptation-boundary checks. The no-broker negative smoke matches v15 §13.7.4.

## Runtime warning

The required PRD was readable, but `preflight.sh read ... codex-headless` could not create its marker under `/home/Uihyeop/agent_setting/.spec-grounding/` because that path is read-only in this worker sandbox. This did not prevent the read-only plan review, but the owner must preserve or satisfy the spec-read guard from an authorized surface before source edits and record the guard result in canonical artifacts.
