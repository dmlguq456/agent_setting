# SD-67 mutation retry lineage implementation plan

governing: prd.md §13.9.1 SD-67

## Scope and invariants

- Route/capability/mode/QA/topology remain the wrapper-validated `autopilot-code`, `dev/refactor`, standard, depth-2 `code-plan` assignment. Do not edit `spec/**`, `capability-route.py`, dispatch-default selectors, permission classification, or SD-68 surfaces.
- Preserve the immutable route pin. A retry consumes the same route record; it must not recompile a route to move `source_commit`.
- Preserve fail-closed behavior for an unset, relative, missing, unreadable, or malformed `AGENT_DISPATCH_JOBS`, a registry without a qualifying prior attempt, and divergent/unrelated history. `_git_state` continues to reject in-progress merge/rebase/cherry-pick and detached HEAD.
- Preserve SD-65 independently: nodes downstream of a mutation keep accepting a first-parent descendant without retry-registry evidence. SD-67 adds a separate, narrower branch for the mutation node itself.
- A qualifying row is a six-field global-registry attempt row for the same `route_id` and `route_node`, has a non-empty `attempt_id`, and differs from the current launch identity when supplied. Row status is not reinterpreted.
- Standard/code QA reports `plan-check:selected-independent-pass:final-verify` with 1 deep + 2 fast reviewers as the selected-pass upper bound. This bounded stage may not dispatch another worker, so the plan-check below is the documented inline fallback.

## Measured baseline

- `worker-route-guard.py::validate_route_contract` currently permits moved HEAD only through `_post_mutation_node(...) && _is_first_parent_descendant(...)`; the mutation node itself therefore requires exact equality.
- `_worktree_mutating_scope` recognizes `source/**` through root `source`, plus `source-scoped` and `target-artifact`.
- `worker_route_guard.test.py` has 8 tests: four SD-65 lineage cases plus valid/scope binding, hash/reselection, generic source mismatch, and non-git state.
- All three wrappers validate the route before resolving the global registry, normalizing/generating `args.attempt_id`, and claiming a row. The current start row is normally absent. The `--register` then `--start --attempt-id ...` path is the exception: its own pre-registered row exists, so an optional current-attempt exclusion is required.
- Reuse `utilities/stage-dispatch-fallback.py::registry_rows`, which already checks the six-tab-field shape and parses exact route/node metadata. Do not add another jobs.log parser.
- The two dev-pipeline references are byte-identical at baseline. Wrapper files are harness-specific, so synchronization means identical guard-argument semantics.
- Planning baseline / safety commit is `fb9a098f`; record the full hash before implementation and do not overwrite it after later commits.

## Implementation checklist

### 1. Core-first contract commit

- [ ] Re-read `core/OPERATIONS.md §5.10`, mark the read, and run write preflight before editing.
- [ ] Immediately after **Canonical global attempt registry under SD-49** and before limit-death handling, add an **SD-67 mutation-node in-place retry** rule: execute FAIL/partial completion may be redispatched on the same route; moved HEAD is accepted only when the node is in `resume_retry_boundaries`, the bound global registry contains a different prior attempt for the same route/node, and HEAD is a first-parent descendant of the original `source_commit`.
- [ ] State that absent/unreadable evidence and divergence retain exact-match rejection; route recompilation/re-pinning and `git reset --hard` restoration are forbidden.
- [ ] Ensure the wording grants neither automatic retry nor extra retry budget and does not alter SD-65 downstream behavior.
- [ ] Commit only `core/OPERATIONS.md` first (`docs(core): define mutation-node retry lineage gate`) and record its hash in `checklist.md` before adapter Skill/reference or wrapper edits.

### 2. Guard implementation and registry evidence

- [ ] Re-read the core commit, then run write preflight for `utilities/worker-route-guard.py`.
- [ ] At the module-loading block, load existing `stage-dispatch-fallback.py` and reuse `registry_rows`; add only imports needed for environment access and fail-closed handling.
- [ ] Beside `_post_mutation_node`, add a direct mutation-node predicate using the selected node's `write_scope` and existing `_worktree_mutating_scope`. Do not infer mutation from a node name.
- [ ] Add a helper that reads only the absolute `AGENT_DISPATCH_JOBS` binding; returns false for unset/non-absolute/non-file/unreadable/malformed input; selects exact route/node rows through `registry_rows`; and requires a non-empty attempt ID different from `current_attempt`.
- [ ] Extend `validate_route_contract(..., current_attempt: str | None = None)` without breaking positional callers. For moved HEAD, allow either the existing SD-65 downstream + first-parent branch or a separate direct-mutation + retry-boundary + prior-evidence + first-parent branch.
- [ ] Retain `route-source-commit-mismatch` and expected/observed detail for all rejected moved HEADs. Add CLI `--current-attempt` and forward it. Do not compile or modify routes.

### 3. Three-wrapper propagation

- [ ] In `validate_route_record`, append `--current-attempt <args.attempt_id>` only when non-empty: Claude around lines 703-724, Codex around 922-944, OpenCode around 795-816.
- [ ] Preserve validation/completion-marker gating before registry resolution, ID generation, and `claim_attempt_row`. Do not move claim earlier.
- [ ] Run write preflight before each wrapper edit and compare all three builders for semantic parity.

### 4. Pipeline reference update and mirror

- [ ] Only after the core-first commit, run write preflight for both reference files.
- [ ] In `adapters/claude/skills/autopilot-code/references/dev-pipeline.md` Step 4, replace item 2's safety-commit lookup and `git checkout <safety-commit> -- <changed paths>` escape hatch with same-route, in-place code-execute redispatch under the SD-67 three-condition gate. Explicitly forbid route recompile/re-pin and `git reset --hard`.
- [ ] Keep the one pipeline retry budget, memo insertion, checklist reset, code-refine decision, re-execute/re-test sequence, and stop-on-second-failure semantics. Remove conductor restoration as a retry prerequisite; do not invent a replacement rollback.
- [ ] Apply the identical change to `skills/autopilot-code/references/dev-pipeline.md`; verify with `cmp -s` and `sha256sum`.

### 5. Guard tests: acceptance plus identity exclusion

- [ ] Run write preflight for `worker_route_guard.test.py`; keep all 8 existing tests. Add helpers for six-field rows and scoped environment bindings to absolute temporary registries.
- [ ] Acceptance ① `test_mutation_retry_descendant_with_prior_attempt_passes`: route at A, execute HEAD at first-parent descendant B, and a different same-route/execute prior attempt pass.
- [ ] Acceptance ② `test_mutation_first_launch_descendant_without_prior_attempt_rejected`: descendant B with empty/nonmatching registry raises `route-source-commit-mismatch`.
- [ ] Acceptance ③a `test_mutation_retry_diverged_head_rejected`: a qualifying row cannot authorize amended/unrelated HEAD. Acceptance ③b `test_mutation_retry_registry_unavailable_rejected`: env unset, missing file, and unreadable/invalid registry subcases retain exact-match failure.
- [ ] Acceptance ④ leave downstream descendant/divergence SD-65 tests registry-free and green; run all original 8 as the regression count.
- [ ] Exclusion `test_mutation_retry_current_attempt_only_rejected`: if the only matching row equals `current_attempt`, descendant execute HEAD rejects. A second assertion may add a different prior row to prove identity-specific exclusion.

### 6. Commit order and verification

- [ ] After the core-only commit, commit guard + tests + three wrappers + two byte-identical references (`fix(dispatch): allow evidence-gated mutation retries`). No adapter/reference commit may precede core.
- [ ] Run `python3 -m py_compile utilities/worker-route-guard.py utilities/worker_route_guard.test.py adapters/{claude,codex,opencode}/bin/dispatch-headless.py`.
- [ ] Required regression suite:
  1. `python3 utilities/worker_route_guard.test.py`
  2. `python3 utilities/dispatch_contract.test.py`
  3. `python3 utilities/dispatch_node.test.py`
  4. `for h in claude codex opencode; do bash adapters/$h/bin/dispatch-headless.sd15.test.sh; done`
  5. `for h in claude codex opencode; do python3 adapters/$h/bin/dispatch-headless.sd45.test.py; done`
  6. `python3 utilities/stage_dispatch_fallback.test.py`
  7. `bash utilities/dispatch-route.test.sh`
- [ ] Byte-compare references, inspect wrapper diffs, run `git diff --check`, and run the adaptation-boundary check when locally available.
- [ ] Final evidence: new acceptance/exclusion tests pass; original 8 pass; required regressions have zero failures; no `spec/**`, `capability-route.py`, SD-68, selector, or permission-classifier diff; core precedes derived commits; no Git operation is in progress.

## Risk review / plan-check

- **Self-evidence:** exclude the current pre-registered attempt exactly and test it.
- **Parser drift:** reuse `registry_rows`; fail closed on read/shape exceptions.
- **SD-65 regression:** keep explicit OR branches and registry-free downstream tests.
- **Over-broad mutation:** classify through existing write-scope vocabulary, never node name.
- **Wrapper timing:** propagate identity only; preserve validation-before-claim.
- **History escape:** reuse `_is_first_parent_descendant` and retain `_git_state` operation guards.
- **Assurance note:** standard QA selects an independent plan-check, but the stage contract forbids dispatch. This inline review is the required fallback evidence.

## Completion gate

The execute handoff is complete only when the core-first commit exists, derived implementation commits follow it, every required regression passes, mirror evidence is recorded, and the checklist contains full safety/core hashes and results. Ambiguous registry evidence, route pinning, or ancestry fails closed.
