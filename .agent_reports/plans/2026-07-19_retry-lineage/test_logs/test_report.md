# SD-67 code-test report — independent cross-harness review (salvaged)

- Reviewer: codex `gpt-5.6-sol` (high effort), deep reviewer, attempt `att-c61046ed5f8e4857b67e78c5b9be909c`.
- Harness independence: execute was claude `sonnet`; test is codex — genuinely independent harness + model.
- **Provenance note:** the codex worker completed its verification but could **not persist this
  artifact** — its `workspace-write` sandbox mounts `/home/Uihyeop/agent_setting/.spec-grounding`
  read-only, so the canonical write preflight hard-blocked the `test_logs/` write and the worker
  ended `BLOCKED`. The conductor salvaged the worker's verified evidence verbatim from its dispatch
  log (`retry-lineage-test.att-c61046ed…codex.jsonl`) into this file. Every command/result below is
  the worker's own; the FAIL finding is the worker's independent judgement, re-confirmed by the
  conductor against the live reference file.

## Verdict: FAIL

Executable implementation is fully correct and green. One **confirmed** documentation/runtime
contradiction in the two byte-identical `dev-pipeline.md` references blocks the code-test gate.

## 1. Commit-order gate — PASS

- `92f25ea0 docs(core): define mutation-node retry lineage gate` touches `core/OPERATIONS.md` only
  and strictly precedes `9b43d754 fix(dispatch): allow evidence-gated mutation retries`.
- Range `fb9a098f..HEAD` touches exactly 8 files (core + guard + tests + 3 wrappers + 2 references).

## 2. Compilation — PASS

`py_compile` on `utilities/worker-route-guard.py`, `utilities/worker_route_guard.test.py`, and all
three `adapters/{claude,codex,opencode}/bin/dispatch-headless.py` — OK.

## 3. Required regression suite (re-run independently, `AGENT_DISPATCH_JOBS` unset) — PASS

- `utilities/worker_route_guard.test.py` → Ran 13 tests, OK
- `utilities/dispatch_contract.test.py` → OK
- `utilities/dispatch_node.test.py` → Ran 17 tests, OK (trailing `dispatch-evidence-no-eligible-fallback` lines are fixture stdout, exit 0)
- `adapters/{claude,codex,opencode}/bin/dispatch-headless.sd15.test.sh` → PASS ×3
- `adapters/{claude,codex,opencode}/bin/dispatch-headless.sd45.test.py` → Ran 9 tests, OK ×3
- `utilities/stage_dispatch_fallback.test.py` → Ran 8 tests, OK
- `utilities/dispatch-route.test.sh` → dispatch-route: PASS
- **Aggregate: 75 Python unittest cases passed, 3 SD-15 shell suites passed, dispatch-route passed. Zero required failures.**

## 4. SD-67 acceptance / exclusion semantics — PASS (genuinely asserted, verified by reading guard + tests)

- A1 `test_mutation_retry_descendant_with_prior_attempt_passes`: first-parent descendant HEAD + absolute registry + different same-route/execute prior attempt + supplied `current_attempt` → validation passes.
- A2 `test_mutation_first_launch_descendant_without_prior_attempt_rejected`: empty registry at descendant HEAD → `route-source-commit-mismatch` with expected/observed detail.
- A3a `test_mutation_retry_diverged_head_rejected`: amended/diverged HEAD stays rejected even with a qualifying row.
- A3b `test_mutation_retry_registry_unavailable_rejected`: env-unset, missing absolute file, relative path, malformed-only registry — all retain exact-match rejection.
- A4: original 8 SD-65/base tests reselected and rerun registry-free — green.
- EX `test_mutation_retry_current_attempt_only_rejected`: a row equal to `current_attempt` alone rejects; a distinct prior row then passes (identity-specific exclusion proven).
- Adversarial: `_qualifying_retry_evidence` catches both `OSError` and `ValueError` (forced each → `False`). Mutation classification uses only node `write_scope` via `_worktree_mutating_scope` (a node named `execute` with `test_logs/**` → non-mutating; an arbitrary name with `source/**` → mutating). Accepted moved-HEAD is a separate OR branch from SD-65 downstream.

## 5. Wrapper parity + claim order — PASS

- All three `validate_route_record` builders append `--current-attempt` only when `args.attempt_id` is non-empty.
- Order confirmed by source line in each wrapper: `validate_route_record` < `new_attempt_id` < claim — claim not moved earlier.
- Reference byte parity: `cmp -s` exit 0; both `sha256 = e900f59b587677bb7493b64a9eeaffdc3c3a6d7ea0c79c55b3091eb30a6d6074`.

## 6. FAILING finding (confirmed) — reference retry wording contradicts the implemented gate

Both `dev-pipeline.md` references, Step 4 item 2 (line 115), state:

> Redispatch code-execute in place on the unchanged route/**attempt**; … the bound canonical
> global registry holds **a different prior attempt** for the same route/node …

This is internally contradictory and inconsistent with the shipped guard:

- The same sentence requires *a different prior attempt*, yet says to retry on the *unchanged attempt*.
- The `--current-attempt` exclusion added in this very cycle removes the current attempt from the
  qualifying set. On a first retry the only matching row **is** that attempt → excluded → guard
  rejects with `route-source-commit-mismatch`.
- Dispatch contract v3's atomic claim treats a reused stable attempt identity as a duplicate and
  starts **no** child (`duplicate_attempt=1`).

**Required correction (fix-forward):** retry on the **unchanged route with a new/different attempt
identity**; the *prior* attempt row is the lineage evidence. Suggested wording: *"Redispatch
code-execute in place on the unchanged route with a new attempt identity."* Apply identically to
both byte-identical references, then re-verify `cmp -s`/`sha256sum` parity and rerun the guard suite.

This cycle's own recovery demonstrates the correct behavior: after the codex execute attempt
`att-bf483834` blocked, execute was redispatched under a **new** attempt `att-e0d7556…` on the
unchanged route — precisely "new attempt identity", not "unchanged attempt".

## 7. Runtime-contract warning (non-blocking)

The canonical PRD was read in full, but codex could not persist the `.spec-grounding` read marker
(read-only outside writable roots). A worktree PRD marker succeeded; the canonical preflight printed
a stale-spec reminder while exiting zero. Recorded, not hidden.
