# quick-depth1-dispatch code-plan

Date: 2026-07-13
Worker: codex depth-2 code-plan under `quick-depth1-impl-r2`
Scope: plan-only file handoff. No source/core/adapter/Fleet/test/projection/generated edits in this stage.

## Spec Significance

spec-significance: SPEC-SIGNIFICANT.

Reason: PRD v6 commit `1d40581` changes the portable runtime topology for autopilot dispatch. It changes core SoT semantics, adapter bootstraps/prompts, generated skill/command projections, Fleet rendering, and guard/test contracts. This is not an implementation detail.

## Stage Graph

Selected graph: `standard` autopilot-code cycle, current worker stage `code-plan` only.

Canonical pipeline remains `code-plan -> code-execute -> code-test -> code-report`. This worker writes only plan artifacts. The next `code-execute` worker should mutate source/docs and generated projections; `code-test` should run the full verification set; `code-report` should update `pipeline_summary.md`.

## Target Semantics

Implement PRD v6:

- `direct`: depth 0 main inline. No plan stage, no depth dispatch.
- `quick`: depth 0 main opens exactly one depth 1 one-shot capability worker. The worker runs `orient-lite -> micro-plan -> plan-check-lite -> produce -> focused verification -> concise report` in one session.
- `quick` depth 2 is forbidden. A quick worker must not launch planner/verifier/stage children.
- Mutation-capable quick work uses an isolated worktree.
- Codex fallback order for quick: headless dispatch first; if unavailable, native subagent with Fleet visibility degradation note; if unavailable, depth 0 inline with concise reason.
- `standard+`: unchanged depth 0 main -> depth 1 conductor -> sequential depth 2 stage-workers with file-only handoff.
- Fleet renders quick depth 1 as one blinking `quick/exec` activity stage, with no plan/test child stages. A quick depth 2 child row is a contract violation.
- Existing validator behavior must remain: quick depth 1 accepted, quick depth 2 rejected.

## Current State Observed

PRD: `.agent_reports/spec/stage-dispatch/prd.md` v6 at commit `1d40581`.

Already partly reflected in current worktree:

- `core/WORKFLOW.md` has uncommitted v6 edits for quick depth-1 one-shot and autopilot-code quick/exec wording.
- `core/CONVENTIONS.md` has uncommitted v6 edits for quick one-shot worker and depth-2 prohibition.
- `core/OPERATIONS.md` has uncommitted v6 edits introducing quick one-shot + isolated worktree, but it still contains a long legacy clause saying `direct/quick 기본 depth2 금지, 스테이지도 inline` inside the standard+ dispatch paragraph. Execution should reconcile this wording so quick is not described as depth-0 inline.

Still stale or likely stale:

- `capabilities/autopilot-code.md` still says quick uses inline micro-plan and `direct|quick` stay inline.
- `capabilities/code-plan.md` still says quick uses caller inline micro-plan.
- Many other capability specs and generated Codex/OpenCode skill projections still carry generic "quick uses inline micro-plan" wording. Decide whether global capability topology now applies to all autopilot entries or only autopilot-code; PRD text says autopilot pipeline, user task asks capabilities/projections broadly.
- `adapters/codex/AGENTS.md` and `adapters/opencode/AGENTS.md` still say `direct/quick` inline in dispatch clauses and autopilot-code route notes.
- `adapters/codex/bin/dispatch-headless.py` generated prompt still says quick uses inline micro-plan plus plan-check-lite and does not mention depth-1 one-shot/fallback.
- `adapters/opencode/bin/dispatch-headless.py` generated prompt has the same stale quick-inline wording.
- `adapters/codex/bin/capability-map.sh` and `adapters/opencode/bin/capability-map.sh` report `plan_policy=direct=no-plan;quick=micro-plan+plan-check-lite;standard+=durable-plan`; this should be extended without breaking downstream parsers, for example `quick=depth1-one-shot-micro-plan+plan-check-lite`.
- `core/HOOKS.md` documents `stage-dispatch-reminder.sh` as soft reminder even though the script and tests implement SD-11b hard deny. Update this drift while touching hook docs.
- `hooks/stage-dispatch-reminder.sh` correctly no-ops for quick; update comments/messages if needed so quick is framed as depth-1 one-shot, not "legit inline" in the main session.
- Fleet already has depth-2 stage worker breadcrumbs; it does not yet appear to have a special quick depth-1 `quick/exec` activity contract.

## Implementation Plan

1. Core SoT alignment first.

   Files: `core/CONVENTIONS.md`, `core/WORKFLOW.md`, `core/OPERATIONS.md`, `core/HOOKS.md`, `core/DESIGN_PRINCIPLES.md` if needed.

   Actions: preserve current uncommitted v6 edits where correct; remove remaining claims that `quick` stays depth-0/main inline; define quick as depth-1 one-shot worker with no depth-2; state mutation quick uses isolated worktree; keep `standard+` stage-dispatch unchanged; update HOOKS SD-11b docs to hard deny for standard+ conductor code-stage calls.

2. Portable capability contracts.

   Files: `capabilities/autopilot-code.md`, `capabilities/code-plan.md`, other `capabilities/autopilot-*.md` with generic quick-inline text if core topology applies family-wide, and `capabilities/README.md` if needed.

   Actions: rewrite autopilot-code artifact/role/stage/procedure text so quick is a depth-1 one-shot capability worker and not a durable `code-plan` stage. For code-plan, state quick micro-plan belongs inside the quick one-shot worker; `code-plan` remains standard+ durable planning only.

3. Compatibility sources and generated projections.

   Sources: Claude mirror skill/bootstrap files, OpenCode command/skill projections, Codex skill/plugin projections.

   Actions: treat Claude files as compatibility/mirror sources, not Codex-native input. Update the source/mirror path used by the repo, then run sync generation so Codex/OpenCode projections are regenerated rather than hand-drifted.

4. Adapter bootstraps and dispatch prompts.

   Files: `adapters/codex/AGENTS.md`, `adapters/opencode/AGENTS.md`, `adapters/claude/CLAUDE.md`, dispatch wrappers, and capability maps.

   Actions: add quick topology to bootstrap dispatch sections; include Codex SD-19 fallback order and Fleet degradation note; keep validator logic rejecting `depth==2 && intensity in {direct,quick}`; preserve model-selection and approval/sandbox behavior.

5. Fleet rendering and collector tests.

   Files: `tools/fleet/render.py`, `tools/fleet/model.py` if needed, `tools/fleet/collectors/dispatch.py` if metadata mapping is insufficient, plus the Claude mirror if required.

   Actions: render a depth-1 quick job with `worker_role=capability-owner`, `intensity=quick`, `capability=<entry>` as one blinking activity stage labeled `quick/exec`; do not render plan/test breadcrumbs for quick depth1; add contract-violation coverage for quick depth2 rows.

6. Guards and tests.

   Files: `hooks/portable-guards.test.sh`, `tools/fleet/tests/test_dispatch.py`, adapter dispatch tests if relevant, boundary/mirror tests if projection drift appears.

   Actions: add deterministic validator tests for quick depth1 accepted and quick depth2 rejected; update prompt-materialization tests to expect quick depth1 one-shot wording; update SDR comments/test labels; add Fleet quick/exec tests.

7. sync-skills/projection generation.

   Run after source edits: Codex native skills/plugin sync, OpenCode native skills/commands sync, and relevant check modes. Prefer the repo's established sync wrapper if `capabilities/sync-skills.md` points to one.

8. Final verification for `code-test` stage.

   Required later: portable guards, Fleet tests, projection checks, boundary/mirror checks, Codex/OpenCode doctor/runtime checks, quick validator probes, and `git diff --check`. Do not run drill unless the main orchestrator explicitly requests it.

## Risks

- Current worktree has uncommitted `core/*.md` changes not made by this worker. `code-execute` must preserve or consciously integrate them, not overwrite.
- `route autopilot-code` still reported missing PRD Read despite actual PRD read and successful marker attempts under `AGENT_HOME=$PWD`; record this as a Codex tool-contract/marker quirk if it persists.
- Generated projections can drift if edited manually. Prefer source edit then sync generation.
- Fleet has both source and Claude mirror copies. Update through the established mirror path or run mirror parity tests after edits.
