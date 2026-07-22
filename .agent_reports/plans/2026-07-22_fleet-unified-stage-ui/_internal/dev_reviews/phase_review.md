## 📋 Code Review Results

**Reviewed files:** independent cross-harness review of the full worktree diff for Fleet v16 (F-36..F-39) — `tools/fleet/{model,route,projection(new),fleet,render,refresh_title,titles}.py`, `tools/fleet/collectors/{__init__,claude,codex,opencode,procscan,dispatch}.py`, the byte-identical `adapters/claude/tools/fleet/**` mirror, and the new/updated test suite under `tools/fleet/tests/`.

**Change summary:** Introduces one additive `WorkProjection`/`ContextProjection` authority (`projection.py`) consumed by all Session/DispatchJob/render/JSON surfaces, replaces per-surface stage judgment (`live_stage()`, first-child selection, PID-only joins) with evidence-precedence resolution and ambiguity codes, collapses inline context gauges into one `ctx … [· NOW]` subordinate row, and raises the title/NOW scheduler quota with OpenCode read-only delta support.

**Verdict:** 🔴 4 issues (2 major) — plan.md's completion gate ("every acceptance row has a named hermetic test and passes") is not yet met; several plan-assigned items the checklist still (correctly) marks open are load-bearing, not cosmetic.

## 🔴 Must-fix issues

### `tools/fleet/render.py:2337-2345` and `:2360-2369` — process-view detail row lands *after* the sub-agent strip, not before it

F-37a/plan step 3.3.6 requires, per active-node/degrade job: **job row → `ctx … [· NOW]` → sub-agent strip**. `_route_card()` (line 2163-2171) already builds `[job_row, subagent_strip]` pairs per active node and returns the finished `card_lines`. The caller then does:

```python
card_lines, meta = _route_card(view, session_by_identity, term_width, now)
for _node in view.get("nodes", []) or []:
    ...
    card_lines.extend(_context_detail_row(_node_job, depth=1, term_width=term_width))
```

`list.extend` appends to the *tail* of the already-built list, so with N active nodes the card reads `job_A, subsA, job_B, subsB, ctx_A, ctx_B` — every context row is batched after every job row and every sub-agent strip, not interleaved. The same pattern repeats for the degrade card (`_degrade_card` already appends its sub-agent strip internally; the caller then appends `detail` after that). Group/plain view gets this right (`render.py:2913-2933` appends the detail row immediately after the job row and *before* the sub-agent-strip append) — only the process view (`p` toggle) has the bug.

Why it matters: this is one of the two F-37 acceptance-matrix rows this whole plan exists to deliver, and it's silently wrong in the higher-density process view specifically. No test catches it — `test_t3_7_active_node_subagent_row_via_pid_join` only asserts membership (`assertIn`), never order, and `test_f37_context_detail.py` has no process-view case at all.

Suggested fix: build each node's `[job_row, ctx_row, *subagent_strip]` as one contiguous chunk inside `_route_card`/`_degrade_card` (where the per-node loop already has `job`/`sess` in scope) instead of doing a second post-hoc pass over `view["nodes"]` in the caller.

### `tools/fleet/projection.py:31,253,290-317` — `owner-route-conflict` never detects the scenario it's named for

Plan step 1.3.5 / checklist Gate A row 31 (checked `[x]`) and round_2 review both state that a direct owner route conflicting with its children's route must fail closed as `multiple-owner-routes` **or** `owner-route-conflict`. In the actual resolver, once an entity has its own explicit route tuple (`_explicit(entity)` true), `resolve_work_projection` returns immediately at line 276-279 (validated) or 281-288 (registry-exact/mismatch) — before children are ever consulted. The owner/child-agreement block (lines 290-317) only runs when the entity has **no** direct tuple of its own, so a direct-owner-vs-child conflict is structurally unreachable. `OWNER_ROUTE_CONFLICT` is defined but only ever emitted by the unrelated recursion guard at line 253 (visiting the same entity twice), which is a same-entity-cycle guard, not an owner/child route-conflict signal.

Why it matters: a depth-1 dispatch job that both carries its own route tuple *and* owns dispatch-depth-2 children with a different route (plausible if stale env or a re-dispatch changes route mid-flight) will silently keep its own route and never surface the conflict, contradicting risk #3 in plan.md and the checked-off checklist row. `test_f36_work_projection.py` has no test for this exact case (`test_owner_rejects_different_child_routes` only covers an owner with *no* direct tuple, i.e. `multiple-owner-routes`), so the gap is untested rather than merely unhandled.

## 🟡 Suggested improvements

- **`tools/fleet/collectors/{claude,codex,opencode}.py`** (e.g. `claude.py:452-456`, `codex.py:738-742`, `opencode.py:247-250`): every collector constructs `ContextEvidence(sequence=X, source_head_sequence=X)` with the *same* value for both fields, computed at the same instant. `projection.normalize_context()`'s `sequence < source_head_sequence` check (the F-38 "reject a stale/regressed sample" contract) can therefore never fire through any real collector — it is only exercised by `test_f38_context_orthogonality.py` via hand-built `ContextEvidence` objects with deliberately different values. The round_2 review's claim that "the private sequence/freshness contract [is] proven for all three harnesses" is true only at the pure-resolver level, not end-to-end. Worth a comment or backlog note so a future contributor doesn't assume this path is live in production.
- **`tools/fleet/demo.py`**: untouched by this change, despite being an explicitly owned Phase-3 file (deterministic `WorkProjection`/composed fork-fan-in demo data, step 3.4). Demo entities still carry only legacy `ctx_pct`; they fall through `projection.py`'s legacy fallback rather than exercising a `route-exact`/composed-DAG projection through the `--once` smoke path. Checklist Gate C row 69 is honestly left unchecked, so this is disclosed, not hidden — but it means the Gate H `--once --view group/process` smoke commands never actually smoke-test a populated `WorkProjection` end to end.
- **Missing test:** no test asserts an "old-key-only" JSON consumer (reading only `sessions`/`jobs`/`summary`/`route`) still succeeds unchanged (plan step 3.1.4, checklist Gate G row 135, acceptance-matrix row "JSON additive"). `grep` across `tools/fleet/tests/` turns up nothing under this name; the additive-shape claim in dev_logs/execute.md rests on manual `json.tool` parsing only, not a pinned regression test.
- **`tools/fleet/model.py`'s `WorkProjection.ambiguity`** is `Optional[str]`, but PRD F-36a's normative shape spells it `ambiguity[]` (array), consistent with `active_nodes[]` beside it. The implementation and its own tests (`test_f36_work_projection.py`) treat it as a single string throughout. Functionally harmless today (only one ambiguity code is ever set at a time), but it is an unacknowledged deviation from the locked schema in a plan whose "Decision points" section says none are permitted without returning to the owner — worth a one-line note either accepting the simplification or fixing the shape.

## 🟢 What is already solid

- `projection.py`'s evidence precedence (validated route+exact tuple → registry-exact → single cwd candidate → artifact-inferred → none) is fail-closed exactly as F-36b requires, and correctly treats any nonempty explicit tuple as a bar to artifact fallback (verified via `test_invalid_explicit_route_fails_closed_over_artifact`).
- `route.py`'s new `load_diagnostic()`/`RouteDiagnostic` cleanly separates "no record" from "explicit invalid," `write_scope` now survives into both `_record_view` and `summary()`, and the old fabricated `{"done":0,"total":0}` progress on unresolved/explicit-invalid routes is gone in favor of `None` — matches F-36d's "never synthesize" contract.
- `collectors/__init__.py`'s `_adopt_child_titles` rewrite is a genuinely atomic association: exact `(harness, pid, proc_start)` first, single-candidate `(harness, realpath(cwd))` fallback only when identity evidence is absent (never as a secondary attempt after an identity match fails), and title/summary/context/`_context_evidence` all move together or not at all — no partial-mix path exists.
- Canonical↔mirror byte parity is real: `diff -rq tools/fleet/ adapters/claude/tools/fleet/ --exclude=__pycache__` returns nothing, and there is no diff at all in `adapters/claude/CLAUDE.md`, any hook, or any adaptation-baseline file — the reported "no task-owned hook/baseline changes" holds up under direct inspection.
- `refresh_title.py`'s quota numbers (`DEFAULT_CONCURRENCY=3`/`MAX_CONCURRENCY=4`, start budget `4/60s`), the 3-6-word/40-char `validate_title`, and the OpenCode mutually-exclusive `--transcript`/`--opencode-db` CLI wiring all match the locked F-39 numbers and the plan's argv contract.

## Review evidence and checks

- Read completely: `plan.md`, `checklist.md`, `_internal/plan_reviews/round_2.md`, `dev_logs/execute.md`, canonical PRD v16 §4.12 (F-36..F-39, acceptance matrix).
- `git status`/`git diff --stat HEAD` enumerated the exact 46 modified + 12 new (6 canonical + 6 mirror) files; matches `dev_logs/execute.md`'s claimed file list exactly.
- `diff -rq tools/fleet/ adapters/claude/tools/fleet/ --exclude=__pycache__` → empty (byte parity confirmed independently, not just trusted from the report).
- `git diff HEAD -- adapters/claude/CLAUDE.md adapters/claude/hooks/` and a baseline-filename grep → empty (no task-owned hook/CLAUDE.md/baseline drift).
- Read `projection.py`, `model.py`, `route.py`, `collectors/{dispatch,__init__,claude,codex,opencode}.py`, and `render.py`/`refresh_title.py`/`titles.py` diffs in full, then traced the two 🔴 findings against their governing plan steps/checklist rows and confirmed via `grep` that no existing test exercises either scenario.
- Cross-checked several checklist rows the executor left unchecked (Gate B row 46, Gate D rows 82-84) against the actual diff: some (Gate B row 46 — preserving terminal `route_file`/`route_hash`/`parent` evidence outside the attempt-contract-validity gate) are in fact implemented and could have been checked off; Gate D rows 82-84 are correctly left open because the process-view ordering bug above is real. The checklist is therefore a conservative but not fully accurate proxy for implementation state — treat individual unchecked rows as "needs verification," not as "definitely missing."
- No source/test file was modified, no commit/push/merge, no live provider invoked by this review.

## Verdict

🔴 Not yet PASS. The two 🔴 items are concrete, reproducible, and tied directly to F-37/F-36 acceptance rows this plan is scoped to deliver; they should go back to the execute stage (or a targeted fix pass) before this attempt is marked complete. The 🟡 items should be resolved or explicitly accepted before final report, since two of them (old-key JSON consumer test, demo.py) are named checklist/plan obligations, not optional polish.
