# Evidence autobind execution checklist

## Guardrails

- [x] Immutable route, worktree, artifact root, source pin, capability, mode, intensity, QA, depth, and write scope confirmed.
- [x] Canonical PRD §13.7.6 and acceptance ③ read; change is within-spec with no spec edit.
- [x] Worktree HEAD confirmed as `5972a61df915815a71b818fec83794a913e2e23e` and source targets were clean during planning.
- [x] Standard code QA policy and inline-review fallback recorded in `plan.md`.
- [x] Before every source/test edit, run `adapters/codex/bin/preflight.sh write <absolute-file> <session-id>` from this worktree.
- [x] Do not edit `loops/drill/cases_growing/g10_claude_opencode_depth2_start/**`, `spec/**`, `capability-route.py`, dispatch-default semantics, authorization classification, or broker cleanup surfaces.

## Implementation

- [x] Refactor `utilities/dispatch-node.py` into testable helpers without changing CLI, route verification, resource-runner behavior, or adapter-argument ordering.
- [x] Select one supported checked tuple by adapter and fallback ordinal; cross-check node candidate against top-level `dispatch_evidence.tuples`.
- [x] Bind the six required wrapper flags and preserve non-empty failure class.
- [x] Accept equal explicit values without duplication; fail before wrapper invocation on explicit/record conflict or conflicting duplicates with both values.
- [x] Prove depth-1 materialization gets no evidence flags and unrelated adapter args remain unchanged.
- [x] Add internal-probe binding to Claude before eligibility/route/registry/launch gates.
- [x] Add internal-probe binding to Codex while preserving session, projection, hook-trust, and nested-network checks.
- [x] Add internal-probe binding to OpenCode while preserving config/runtime and limit behavior.
- [x] Probe only absent depth-2 start evidence; explicit/partial evidence, depth 1, dry-run, and register do not probe.
- [x] Validate JSON identity exactly; never infer supported from process return code; retain unsupported and malformed/error results as fail-closed.
- [x] Record `eligibility_probe=internal` and resolved tuple in successful output/jobs pipe and structured failure output where no row may be claimed.
- [x] Preserve `utilities/nested-dispatch-eligibility.py` auth/network/classification semantics (unmodified).

## New and expanded tests

- [x] Create `utilities/dispatch_node.test.py` for binding, fallback selection, equal explicit values, conflicts, ambiguity/missing evidence, and depth-1 invariance.
- [x] Expand Claude SD-45 tests for internal supported/unsupported, explicit-no-probe, invalid identity, output, and registry evidence.
- [x] Expand Codex SD-45 tests with the same cases and Codex constraints intact.
- [x] Expand OpenCode SD-45 tests with the same cases and OpenCode constraints intact.
- [x] Probe utility (`utilities/nested-dispatch-eligibility.py`) was not refactored — no extraction was needed, direct tests unchanged.

## Verification commands (task worktree only)

- [x] `python3 utilities/dispatch_node.test.py` — OK, 17 tests
- [x] `python3 utilities/dispatch_contract.test.py` — OK, 10 tests
- [x] `bash adapters/claude/bin/dispatch-headless.sd15.test.sh` — PASS
- [x] `bash adapters/codex/bin/dispatch-headless.sd15.test.sh` — PASS
- [x] `bash adapters/opencode/bin/dispatch-headless.sd15.test.sh` — PASS
- [x] `python3 adapters/claude/bin/dispatch-headless.sd45.test.py` — OK, 9 tests
- [x] `python3 adapters/codex/bin/dispatch-headless.sd45.test.py` — OK, 9 tests
- [x] `python3 adapters/opencode/bin/dispatch-headless.sd45.test.py` — OK, 9 tests
- [x] `python3 utilities/stage_dispatch_fallback.test.py` — OK, 7 tests
- [x] `python3 utilities/nested_dispatch_eligibility.test.py` — OK, 4 tests
- [x] `bash utilities/dispatch-route.test.sh` — PASS
- [x] `python3 -m py_compile utilities/dispatch-node.py utilities/nested-dispatch-eligibility.py adapters/claude/bin/dispatch-headless.py adapters/codex/bin/dispatch-headless.py adapters/opencode/bin/dispatch-headless.py utilities/dispatch_node.test.py adapters/claude/bin/dispatch-headless.sd45.test.py adapters/codex/bin/dispatch-headless.sd45.test.py adapters/opencode/bin/dispatch-headless.sd45.test.py` — OK
- [x] `git diff --exit-code -- loops/drill/cases_growing/g10_claude_opencode_depth2_start spec` — clean
- [x] `git diff --check` — clean

Note: all subprocess-based `*.sd45.test.py` cases were also run with
`AGENT_DISPATCH_JOBS` unset — see `dev_logs/execute.md` "Deviation" for why
(this stage is itself a nested worker that inherits a real global registry
path, which collides with the tests' own `--jobs` fixture under SD-49,
independent of any change in this cycle; confirmed via `git stash` against
unmodified HEAD).

## Completion evidence

- [x] Record changed files, decisions, outputs, and warnings in canonical `dev_logs/**` and update this checklist.
- [ ] Test stage confirms every command ran inside `/home/Uihyeop/agent_setting-wt/evidence-autobind` and stores logs under the canonical artifact root.
- [ ] Test stage confirms unsupported/unknown/missing evidence never claims a row or launches a child.
- [ ] Depth-0 integration owner runs the unchanged g10 drill after harvest; this stage does not edit or run it.
