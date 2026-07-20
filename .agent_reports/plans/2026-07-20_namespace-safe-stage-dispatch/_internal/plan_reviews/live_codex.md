# Live Codex foreground transport review

## Identity and scope

- Route: `rt-0734fbe82e718115` (`AGENT_ROUTE_ID`)
- Node: `plan` (`AGENT_ROUTE_NODE`)
- Attempt: `att-livecodex000000000000000000000000000000000000000002`
- Registry row slug: `namespace-safe-live-codex-r2`
- Parent: `namespace-safe-stage-dispatch-owner`; parent session `019f7d9e-2e96-7371-88b4-2b9e6b272cee`
- Runtime: Codex headless depth-2 stage, `code-plan`, strong intensity, standard code QA
- Worktree: `/home/Uihyeop/agent_setting-wt/namespace-safe-stage-dispatch`
- Canonical artifact root: `/home/Uihyeop/agent_setting/.agent_reports`

`AGENT_ROUTE_ID` and `AGENT_ROUTE_NODE` were present in the worker environment. The exact attempt was bound by the assigned heartbeat command and the matching canonical jobs row; no dedicated attempt-id environment variable was exposed to the child.

## Review result

**Verdict: PASS.** The current implementation matches the approved plan for namespace-safe stage dispatch, and the live Codex foreground-scoped wrapper lifetime reached and sustained this worker.

The exact attempt row remained `open` while this review ran and recorded `launch_lifecycle=foreground-scoped`, `pid_scope=namespace-local`, `pid=434`, and `pid_start=834782`. The child environment reported `AGENT_DISPATCH_CURRENT_HARNESS=codex`, `AGENT_DISPATCH_CURRENT_TRANSPORT=headless`, and the expected effective `danger-full-access` inner runtime sandbox. Successful stage-heartbeat updates advanced from sequence 2 through sequence 9 during real reads and tests. Together, the still-live exact row and advancing worker heartbeats demonstrate that the foreground-scoped wrapper call did not return and tear down the PID namespace before this worker completed.

## Approved-plan comparison

- The prior detached fail-fast guard is retained and is now conditional on the detached lifecycle.
- `core/OPERATIONS.md` defines transient-namespace `foreground-scoped` behavior, durable-scope detached compatibility, exact-row failure closure, parent identity, Fleet orphan visibility, and the checked outer-sandbox boundary.
- `utilities/dispatch_lifecycle.py` supplies shared namespace detection, lifecycle selection, timeout handling, signal forwarding, and typed child outcomes; the Claude adapter has the matching projected utility.
- Codex and Claude wrappers accept the lifecycle/timeout contract, annotate the exact attempt row and machine-readable output, wait in foreground scope, classify timeout/signal/non-zero exit, and retain detached early-death behavior.
- `utilities/stage-dispatch-fallback.py` selects and projects the lifecycle, waits with a foreground-aware timeout, treats `worker_failure` as a failed candidate, defaults the logical parent from wrapper identity, and rejects parent mismatch.
- Codex foreground children under the checked Codex outer sandbox use and report the effective inner `danger-full-access` runtime sandbox, matching the plan's nested-mount workaround without widening the outer authority.
- Deterministic coverage exists for lifecycle detection/override, foreground completion, signal/timeout handling, wrapper projection, exact attempt closure, detached compatibility, and foreground wrapper output. Fleet coverage keeps unmatched depth-2 rows visible as orphans.
- The canonical PRD was not modified by this stage; the approved transaction-only boundary remains intact.

## Changed-file observations

The final worktree snapshot contained 15 changed or untracked source/test files, all aligned with the approved dispatch-lifecycle work:

- Contracts/docs: `core/OPERATIONS.md`, `adapters/codex/ADAPTATION.md`, `adapters/claude/ADAPTATION.md`.
- Wrapper/runtime implementation: `adapters/codex/bin/dispatch-headless.py`, `adapters/claude/bin/dispatch-headless.py`, `utilities/stage-dispatch-fallback.py`, `utilities/dispatch_lifecycle.py`, `adapters/claude/utilities/dispatch_lifecycle.py`.
- Fleet orphan visibility: `adapters/claude/tools/fleet/render.py`.
- Verification/projection: `utilities/dispatch_lifecycle.test.py`, `adapters/claude/utilities/dispatch_lifecycle.test.py`, `utilities/stage_dispatch_fallback.test.py`, `utilities/dispatch_adapters_v11.test.py`, `adapters/claude/tools/fleet/tests/test_f15_rows.py`, `tools/check-adaptation-boundary.sh`.

No source, `plan.md`, `checklist.md`, route, or canonical PRD file was edited by this review worker.

## Commands and evidence

- `preflight.sh stage-heartbeat ... --phase analysis --kind registry --evidence analysis-entered` and subsequent tool/test heartbeats: all `check=ok`; final observed sequence 9.
- `cat .../skills/code-plan/SKILL.md`; `preflight.sh mode-info dev/refactor`; `cat adapters/codex/modes/dev/refactor.md`: assigned stage and native mode contracts read.
- `preflight.sh qa-policy standard code`: required assurance was `plan-check:selected-independent-pass:final-verify`; this independently launched review is the selected pass, with deterministic final verification below.
- `rg --files` in the plan artifact directory; `cat .../plan.md`: approved plan located and read without modification.
- `git status --short`, `git diff --stat`, full/per-file `git diff`, and reads of the four new lifecycle utility/test files: implementation and final changed-file scope inspected.
- Filtered `env` inspection and `rg` of the exact attempt in `$AGENT_DISPATCH_JOBS`: route/node/parent/runtime identity and live foreground row confirmed.
- `preflight.sh verification-runner --timeout 120 -- python3 utilities/dispatch_lifecycle.test.py`: 5 passed.
- `preflight.sh verification-runner --timeout 120 -- python3 adapters/claude/utilities/dispatch_lifecycle.test.py`: 5 passed.
- `preflight.sh verification-runner --timeout 120 -- python3 utilities/stage_dispatch_fallback.test.py`: 10 passed.
- First in-worker run of `utilities/dispatch_adapters_v11.test.py`: 8 passed, 1 failed because the live worker's inherited `CODEX_DISPATCH_SANDBOX_FORCE=danger-full-access` changed a fixture that asserts the normal depth-1 `workspace-write` default. This was environment contamination, not a product failure.
- Clean rerun through the verification runner with `CODEX_DISPATCH_SANDBOX_FORCE`, inherited registry, and current-child identity variables removed: 9 passed.
- `preflight.sh verification-runner --timeout 120 -- python3 -m unittest adapters.claude.tools.fleet.tests.test_f15_rows`: 37 passed.
- Clean focused verification total: 66 passed. `git diff --check`: passed.

## QA assurance and warnings

Standard code QA asks for one selected independent pass when available and final verification. This route delivered the review through a distinct foreground-scoped Codex depth-2 worker, and the focused suites plus whitespace validation passed. No additional worker was dispatched, as prohibited by the stage kernel. The only observed failing test invocation was reproduced as inherited-environment contamination and passed under its intended clean fixture environment.
