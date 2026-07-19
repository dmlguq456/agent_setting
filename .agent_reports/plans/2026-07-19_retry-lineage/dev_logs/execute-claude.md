# SD-67 code-execute dev log (claude re-dispatch)

Resume context: prior codex execute worker BLOCKED — codex `workspace-write` sandbox mounted the
linked worktree's git metadata read-only, so `git commit` could not create `index.lock`. That
worker had already applied a correct, complete section-1 edit to `core/OPERATIONS.md` (uncommitted).
This claude re-dispatch verified that edit against `plan.md` §1 and `prd.md` §13.9.1 and found it
complete — no rewrite needed, proceeded straight to commit.

## 1. Core-first commit

- `git diff core/OPERATIONS.md` reviewed: the pre-existing SD-67 bullet already covers the
  three-condition gate (`resume_retry_boundaries` declaration, different prior registry attempt for
  same route/node, first-parent descendant of `source_commit`), fail-closed on absent/unreadable
  evidence and divergence, forbids route recompile/re-pin and `git reset --hard`, and states no
  auto-retry/no extra budget and no change to SD-65.
- Cross-checked verbatim against `prd.md:927-931` (SD-67 contract) — matches.
- `git add core/OPERATIONS.md && git commit -m "docs(core): define mutation-node retry lineage gate"`
  → commit `92f25ea04121ada80d8fd50efba51b904b7cc4a5`.
- Recorded hash in `checklist.md` before any adapter/Skill edit.

## 2. Guard implementation (`utilities/worker-route-guard.py`)

- Imported `stage-dispatch-fallback.py` via `importlib` (module `stage_dispatch_fallback`) to reuse
  `registry_rows` — no new jobs.log parser.
- Added `_direct_mutation_node(node)` — reuses existing `_worktree_mutating_scope` over the node's
  `write_scope`; no classification by node name.
- Added `_qualifying_retry_evidence(route_id, node_id, current_attempt)` — reads only
  `os.environ["AGENT_DISPATCH_JOBS"]`; fails closed (`False`) on unset, non-absolute, non-file, or a
  `registry_rows` read/parse exception (`OSError`/`ValueError`); requires a non-empty `attempt_id`
  different from `current_attempt`.
- Extended `validate_route_contract(..., current_attempt: str | None = None)` — appended as the last
  parameter so all existing positional callers are unaffected.
- Moved-HEAD branch now accepts either the existing SD-65 `downstream_ok` path (post-mutation node +
  first-parent descendant) OR a new `mutation_retry_ok` path (direct mutation node + node in
  `resume_retry_boundaries` + qualifying registry evidence + first-parent descendant). Both branches
  still raise `route-source-commit-mismatch` with `expected=.../observed=...` detail when neither
  qualifies.
- Added CLI `--current-attempt` and forwarded it into `validate_route_contract`.
- Did not touch route compilation/modification logic.

## 3. Wrapper propagation (3 adapters)

- `adapters/claude/bin/dispatch-headless.py` (~line 715), `adapters/codex/bin/dispatch-headless.py`
  (~line 935), `adapters/opencode/bin/dispatch-headless.py` (~line 805): in `validate_route_record`,
  append `--current-attempt <args.attempt_id>` to the guard invocation only when `args.attempt_id` is
  non-empty. Confirmed all three call `validate_route_record` before global-registry
  resolution/`new_attempt_id`/`claim_attempt_row` — claim order unchanged. Diffs are line-for-line
  identical in shape across all three wrappers (semantic parity).

## 4. Pipeline reference update + mirror

- `adapters/claude/skills/autopilot-code/references/dev-pipeline.md` Step 4 item 2: replaced the
  `Safety commit: {hash}` / `git checkout <safety-commit> -- <paths>` escape hatch with same-route
  in-place code-execute redispatch under the SD-67 three-condition gate; explicitly states "do not
  restore or roll back source" and "never run `git reset --hard`" and "never recompile or re-pin the
  route." Items 1, 3-7 (memo, checklist reset, refine decision, redispatch/re-test sequence,
  stop-on-second-failure) unchanged.
- Applied the identical edit to `skills/autopilot-code/references/dev-pipeline.md`.
- Verified: `cmp -s adapters/claude/skills/autopilot-code/references/dev-pipeline.md
  skills/autopilot-code/references/dev-pipeline.md` → identical;
  `sha256sum` both → `e900f59b587677bb7493b64a9eeaffdc3c3a6d7ea0c79c55b3091eb30a6d6074` (both).

## 5. Guard tests (`utilities/worker_route_guard.test.py`)

Kept all 8 original tests unchanged. Added helpers `_write_registry_row` (writes a six-tab-field
registry row) and `_bound_jobs` (context manager scoping `AGENT_DISPATCH_JOBS` to an absolute temp
path, restoring the prior value on exit). Added:
- `test_mutation_retry_descendant_with_prior_attempt_passes` (A1)
- `test_mutation_first_launch_descendant_without_prior_attempt_rejected` (A2)
- `test_mutation_retry_diverged_head_rejected` (A3a)
- `test_mutation_retry_registry_unavailable_rejected` (A3b — env-unset/missing-file/relative-path/
  malformed-rows subcases via `subTest`)
- `test_mutation_retry_current_attempt_only_rejected` (EX — self-evidence exclusion, then a second
  assertion with a distinct prior row proving identity-specific exclusion)

Result: 13/13 pass (`python3 utilities/worker_route_guard.test.py` → `Ran 13 tests ... OK`).

## 6. Commits and verification

- Commit order: `92f25ea0...` (core-only) precedes `9b43d754...` (derived implementation:
  guard + tests + 3 wrappers + 2 byte-identical references, message
  `fix(dispatch): allow evidence-gated mutation retries`).
- `python3 -m py_compile utilities/worker-route-guard.py utilities/worker_route_guard.test.py
  adapters/{claude,codex,opencode}/bin/dispatch-headless.py` → OK, no errors.
- Required regression suite (all run with `AGENT_DISPATCH_JOBS` explicitly unset in the shell, since
  this worker's own dispatch inherited that variable from the parent conductor and it would otherwise
  leak into the SD-49 canonical-registry check inside the sd45 fixtures — this is shell-environment
  hygiene, not a code change):
  - `python3 utilities/worker_route_guard.test.py` → `Ran 13 tests ... OK`
  - `python3 utilities/dispatch_contract.test.py` → `Ran 10 tests ... OK`
  - `python3 utilities/dispatch_node.test.py` → `Ran 17 tests ... OK` (trailing
    `check=failed reason=dispatch-evidence-no-eligible-fallback adapter=codex` lines are expected
    fixture stdout captured by the test, not a failure — exit code 0)
  - `bash adapters/claude/bin/dispatch-headless.sd15.test.sh` → PASS
  - `bash adapters/codex/bin/dispatch-headless.sd15.test.sh` → PASS
  - `bash adapters/opencode/bin/dispatch-headless.sd15.test.sh` → PASS
  - `python3 adapters/claude/bin/dispatch-headless.sd45.test.py` → `Ran 9 tests ... OK`
  - `python3 adapters/codex/bin/dispatch-headless.sd45.test.py` → `Ran 9 tests ... OK`
  - `python3 adapters/opencode/bin/dispatch-headless.sd45.test.py` → `Ran 9 tests ... OK`
  - `python3 utilities/stage_dispatch_fallback.test.py` → `Ran 8 tests ... OK`
  - `bash utilities/dispatch-route.test.sh` → `dispatch-route: PASS`
- `git diff --check` → clean (no whitespace errors).
- Reference byte parity re-confirmed after final commit (see §4).
- Changed files (final commit `9b43d754...`): `utilities/worker-route-guard.py`,
  `utilities/worker_route_guard.test.py`, `adapters/claude/bin/dispatch-headless.py`,
  `adapters/codex/bin/dispatch-headless.py`, `adapters/opencode/bin/dispatch-headless.py`,
  `adapters/claude/skills/autopilot-code/references/dev-pipeline.md`,
  `skills/autopilot-code/references/dev-pipeline.md`.
- Out-of-scope surfaces confirmed untouched: no `spec/**`, no `capability-route.py`, no
  SD-68/selector/permission-classifier diff (`git diff --stat` against the commit range shows only
  the 7 files above).

## Gate

Core-first commit exists and precedes the derived commit; all required regressions pass with zero
failures; mirror byte-parity recorded; checklist hashes recorded. Verdict: PASS.
