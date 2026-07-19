# SD-67 mutation-node retry lineage — final report

> **Round-2 addendum (depth-0 fix-forward, 2026-07-19)**: the single blocking finding below
> was fixed by commit `9196282a` (both dev-pipeline.md mirrors: "unchanged route/attempt" →
> "unchanged route with a new attempt identity"; byte parity restored, `fab3c811…`) and
> independently re-verified — 13 guard tests, full dispatch suites, SD-45/SD-15 ×3, boundary
> guard all green (`test_logs/verification_round2.md`). **Cycle verdict after round 2: PASS.**
> The round-1 FAIL record below is preserved intact.

- Capability: autopilot-code (dev/refactor), intensity standard, staged depth-2, tracked within-spec.
- Governing spec: `spec/stage-dispatch/prd.md §13.9.1 SD-67`.
- Route: `rt-e6ed0326b81b2778` (immutable, `source_commit fb9a098f`), worktree `retry-lineage`.
- **Verdict: FAIL** — implementation is correct and fully green, but an independent cross-harness
  reviewer found one confirmed documentation/runtime contradiction that blocks the code-test gate.
  Per the route binding (execute-retry situations close honestly, no `git reset --hard`, no unproven
  extra retry round), the cycle is closed FAIL with a precise fix-forward list rather than looped.

## What was built (commits on `retry-lineage`)

1. `92f25ea0 docs(core): define mutation-node retry lineage gate` — **core-only, committed first.**
   `core/OPERATIONS.md §5.10` gains the SD-67 in-place retry rule: a mutation node may be
   redispatched on the same immutable route; moved `HEAD` is accepted only when the node is in
   `resume_retry_boundaries`, the bound canonical registry holds a *different prior attempt* for the
   same route/node, and `HEAD` is a first-parent descendant of `source_commit`. Missing/unreadable
   evidence and divergence keep exact-match rejection; route recompile/re-pin and `git reset --hard`
   forbidden; no auto-retry, no extra budget; SD-65 downstream unchanged.
2. `9b43d754 fix(dispatch): allow evidence-gated mutation retries` — derived, follows core:
   - `utilities/worker-route-guard.py`: reuses `stage-dispatch-fallback.py::registry_rows` (no new
     parser); `_direct_mutation_node` classifies via node `write_scope` + `_worktree_mutating_scope`
     (never by node name); `_qualifying_retry_evidence` reads only the absolute `AGENT_DISPATCH_JOBS`,
     fails closed on unset/non-absolute/non-file/unreadable/malformed and requires a non-empty
     `attempt_id != current_attempt`; `validate_route_contract(..., current_attempt=None)` adds a
     separate OR branch and a `--current-attempt` CLI, keeping positional callers intact.
   - Three wrappers `adapters/{claude,codex,opencode}/bin/dispatch-headless.py`: append
     `--current-attempt` only when non-empty; claim order unchanged (validate < id-gen < claim).
   - Both `dev-pipeline.md` references updated (byte-identical, sha256 `e900f59b…`).
   - `utilities/worker_route_guard.test.py`: 8 original tests kept + A1/A2/A3a/A3b/EX added (13 total).

## Verification (independent, codex reviewer)

- 75 Python unittest cases + 3 SD-15 shell suites + `dispatch-route` — **all pass, zero failures.**
- All six SD-67 acceptance/exclusion assertions genuinely present and correct; adversarial checks on
  fail-closed exception handling and scope-based (not name-based) mutation classification pass.
- Reference byte parity holds; out-of-scope surfaces (`spec/**`, `capability-route.py`, SD-68,
  selector, permission-classifier) untouched. Full detail: `test_logs/test_report.md`.

## Why FAIL — the one blocking finding

`dev-pipeline.md` (both mirrors), Step 4 item 2, line 115:

> "Redispatch code-execute in place on the unchanged route/**attempt** … holds **a different prior
> attempt** …"

Self-contradictory and inconsistent with the shipped guard: the `--current-attempt` exclusion (added
this cycle) removes the current attempt from the qualifying set, so a retry on the *unchanged
attempt* is rejected; v3's atomic claim also treats a reused attempt id as a duplicate (no child).
The prose should require a **new attempt identity** on the unchanged route, with the prior attempt
row as lineage evidence. The executable code already enforces the correct rule — only the two
reference prose lines are wrong.

## Fix-forward list (to reach PASS)

1. In **both** `adapters/claude/skills/autopilot-code/references/dev-pipeline.md` and
   `skills/autopilot-code/references/dev-pipeline.md`, Step 4 item 2: replace "on the unchanged
   route/attempt" with "on the unchanged route **with a new attempt identity**" (prior attempt row =
   lineage evidence). Keep the rest of the SD-67 three-condition sentence unchanged.
2. Re-verify `cmp -s` + `sha256sum` byte parity of the two references.
3. Rerun `python3 utilities/worker_route_guard.test.py` (+ `git diff --check`) to confirm no
   regression; the change is prose-only so all suites should stay green.
4. Amend/extend the derived commit (fix-forward, **no `git reset --hard`**), then code-test → report.

## SD-64 orphan / replacement history (honest record)

- Original conductor dispatched `plan` then died ending its turn to "wait" — orphaned under `claude -p`
  one-shot semantics. depth-0 recovery closed the plan row and wrote its completion marker.
- This replacement conductor resumed from the route record + `plan` marker (plan not re-run) and ran
  execute → test.
- **execute attempt 1 (codex `att-bf483834`) BLOCKED**: codex `workspace-write` sandbox mounts the
  linked-worktree git metadata read-only → `git commit` could not create `index.lock`. The worker
  correctly refused (no `git reset`), leaving a correct uncommitted `core/OPERATIONS.md` edit.
- Harness re-selected **codex → claude** for execute (recorded reason: codex sandbox cannot write
  linked-worktree git metadata; the user account itself is writable — verified). The claude
  re-dispatch (`att-e0d7556…`, new attempt id, unchanged route) verified and committed the existing
  core edit, then completed sections 2–6 → PASS.
- **test (codex `att-c61046ed`)** ran full verification but ended BLOCKED on artifact persistence
  (`.spec-grounding` read-only); the conductor salvaged its verified evidence into `test_logs/`.
- Two codex attempt rows (`att-bf483834`, `att-c61046ed`) remain `open` in the registry: they are
  namespace-local with no terminal heartbeat (sandbox could not write heartbeats), so
  `dispatch-registry.py reconcile` conservatively declines to auto-close them. Both are harvested and
  terminal in fact (recorded host pids dead, terminal messages in their logs); left as audit records.
- Environmental lesson: **codex depth-2 workers cannot reliably complete artifact/commit-producing
  stages in this linked-worktree + read-only-`.spec-grounding` setup**; claude workers are unaffected.

## Out-of-scope (untouched, as required)

SD-68 config sealing, selector-path repair, permission classifier, `spec/**`, `capability-route.py`
compile changes.
