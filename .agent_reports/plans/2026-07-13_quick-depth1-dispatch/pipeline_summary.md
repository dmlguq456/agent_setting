# Pipeline Summary - quick-depth1-dispatch

- **Stage**: `code-report`
- **Worker**: codex depth-2 under `quick-depth1-impl-r2`
- **Scope**: report-only handoff. No source or generated projection edits in this stage.
- **Spec**: `.agent_reports/spec/stage-dispatch/prd.md`
- **Verdict**: quick-depth1 contract evidence is clean; remaining boundary/runtime failures are pre-existing Claude adapter debt, not quick-depth1 regressions.

## Changed File Groups

### Core SoT and portable contracts
- `core/CONVENTIONS.md`
- `core/OPERATIONS.md`
- `core/WORKFLOW.md`
- `capabilities/autopilot-*.md`
- `capabilities/code-plan.md`
- `capabilities/README.md`

Key semantics implemented by the cycle:
- `direct` stays depth-0 inline.
- `quick` is now a depth-1 one-shot capability worker with `micro-plan -> plan-check-lite -> focused verification -> concise report`.
- `quick` depth-2 is forbidden.
- `standard+` retains `code-plan -> code-execute -> code-test -> code-report`.
- quick mutation work uses an isolated worktree.

### Adapter bootstraps, projections, and dispatch plumbing
- `adapters/codex/AGENTS.md`
- `adapters/codex/bin/capability-map.sh`
- `adapters/codex/bin/dispatch-headless.py`
- `adapters/codex/skills/autopilot-*.md`
- `adapters/codex/plugins/agent-harness-codex/skills/autopilot-*.md`
- `adapters/opencode/AGENTS.md`
- `adapters/opencode/bin/capability-map.sh`
- `adapters/opencode/bin/dispatch-headless.py`
- `adapters/claude/CLAUDE.md`
- `adapters/claude/skills/**`

Key semantics implemented by the cycle:
- adapter bootstraps now describe the quick depth-1 one-shot route instead of stale quick-inline wording.
- generated Codex/OpenCode skill projections were regenerated from the portable capability sources.
- dispatch prompts and capability maps now expose the depth-1 quick policy.

### Fleet rendering, hooks, and tests
- `tools/fleet/render.py`
- `tools/fleet/tests/test_dispatch.py`
- `hooks/stage-dispatch-reminder.sh`
- `hooks/portable-guards.test.sh`
- `tools/check-adaptation-boundary.sh`

Key semantics implemented by the cycle:
- Fleet renders quick depth-1 as a single `quick/exec` activity breadcrumb.
- quick depth-1 does not render plan/test child stages.
- quick depth-2 remains a contract violation in validator coverage.
- boundary checks now expect the current quick policy string.

### Report artifacts
- `.agent_reports/plans/2026-07-13_quick-depth1-dispatch/plan.md`
- `.agent_reports/plans/2026-07-13_quick-depth1-dispatch/checklist.md`
- `.agent_reports/plans/2026-07-13_quick-depth1-dispatch/dev_logs/step_01_execute.md`
- `.agent_reports/plans/2026-07-13_quick-depth1-dispatch/dev_logs/step_02_execute_fix.md`
- `.agent_reports/plans/2026-07-13_quick-depth1-dispatch/test_logs/verification.md`
- `.agent_reports/plans/2026-07-13_quick-depth1-dispatch/test_logs/verification_rerun.md`
- `.agent_reports/plans/2026-07-13_quick-depth1-dispatch/pipeline_summary.md`

## Verification Commands and Results

### Quick-contract evidence
- `adapters/codex/bin/preflight.sh capability-info autopilot-code`
  - `plan_policy=direct=no-plan;quick=depth1-one-shot-micro-plan+plan-check-lite;standard+=durable-plan`
  - `dispatch_contract=preflight.sh dispatch --capability autopilot-code --mode <family/mode> --qa <level> --intensity <level> --depth 1|2`
- `python3 tools/fleet/tests/test_dispatch.py`
  - passed
  - quick depth-1 accepted, quick depth-2 rejected

### Passed checks
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- python3 tools/fleet/tests/test_dispatch.py`
  - `status=ok`
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- python3 tools/fleet/tests/test_mirror_parity.py`
  - `status=ok`
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- python3 adapters/codex/bin/sync-native-skills.py --check`
  - `status=ok`
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- python3 adapters/codex/bin/sync-native-plugin.py --check`
  - `status=ok`
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- python3 adapters/opencode/bin/sync-native-skills.py --check`
  - `status=ok`
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- python3 adapters/opencode/bin/sync-native-commands.py --check`
  - `status=ok`
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- git diff --check`
  - `status=ok`

### Mixed or pre-existing failures
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- bash hooks/portable-guards.test.sh`
  - still reports unrelated existing BAD cases outside the quick depth-1/2 contract path
  - the isolated quick depth-1 and quick depth-2 wrapper checks pass
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- bash tools/check-adaptation-boundary.sh`
  - fails on existing Claude boundary debt
  - `FAIL: adapters/claude/loops/drill/cases_growing/g_stage_dispatch is missing`
  - `FAIL: adapters/claude/tools/install is missing`
  - `FAIL: adapters/claude/tools/memory/mem_cluster_j.test.sh is missing`
  - `WARN: 58 concrete Claude/model references remain in portable areas`
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- adapters/codex/bin/preflight.sh doctor`
  - `check=adaptation-boundary:failed`
  - `status=failed`
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- adapters/codex/bin/preflight.sh doctor --runtime`
  - `check=bootstrap:failed reason=codex-debug-failed exit=1`
  - `status=failed`
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- adapters/codex/bin/preflight.sh runtime-projection`
  - `check=runtime-projection:skipped`
  - `status=failed`
- `adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- adapters/opencode/bin/preflight.sh doctor`
  - `check=adaptation-boundary:failed`
  - `status=failed`

## Tool Contracts and Adapter Quirks

- `route autopilot-code . codex-headless` still reports a missing PRD read marker for `./.agent_reports/spec/prd.md` even after the stage-dispatch PRD has been read and marked; this is a relative-path marker quirk in the route gate.
- `apply_patch` is usable only after the explicit write gate on guarded paths; durable edits were routed through `adapters/codex/bin/preflight.sh write <file> codex-headless` before patching.
- `capability-info code-report` is instruction-only on Codex; it does not expose a separate runtime tool contract beyond the native skill/plugin projection.

## Remaining Failing Checks

These are pre-existing Claude boundary/runtime debt and are out of scope for quick-depth1:
- missing Claude mirror files in `tools/check-adaptation-boundary.sh`
- lingering concrete Claude/model references in portable areas
- `doctor --runtime` bootstrap/runtime-projection failures
- `opencode doctor` boundary failure

## Artifacts

- Report path: `.agent_reports/plans/2026-07-13_quick-depth1-dispatch/pipeline_summary.md`
- Supporting plan artifacts: `plan.md`, `checklist.md`, `dev_logs/step_01_execute.md`, `dev_logs/step_02_execute_fix.md`
- Verification artifacts: `test_logs/verification.md`, `test_logs/verification_rerun.md`
