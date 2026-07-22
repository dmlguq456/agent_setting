# Fleet v16 owner pipeline report

## Verdict

**PASS.** The approved `autopilot-code` pipeline reached a signed execute
marker, the independent implementation review found and the correction cycle
fixed two major v16 acceptance defects, and a **fresh** independent
cross-harness implementation review plus a **fresh** final test stage both
returned PASS from the current worktree. `code-report` (this artifact) is the
final stage. No commit, push, merge, or cleanup has occurred.

## Immutable route and assurance

- Route: `rt-dfec3aabe921b37f`
- Route hash: `sha256:dfec3aabe921b37fa9da8973c530b48ea92b7a9cd8fa9cdff7a7dd950512d404`
- Capability/mode/intensity/QA: `autopilot-code` / `dev/refactor` / strong / standard
- Required assurance: `plan-check:selected-independent-pass:final-verify` — **met**.
- Pipeline: `code-plan -> code-execute -> code-test -> code-report`, with an
  independent implementation review inserted at the riskiest point.

## Stage outcomes

| Stage | Outcome | Durable evidence |
|---|---|---|
| code-plan | PASS, signed marker | `plan/plan.md`, `plan/checklist.md` |
| plan-check round 1 | FAIL, independent Codex + Claude findings | `_internal/plan_reviews/round_1.md` |
| code-refine | PASS | revised `plan/plan.md` and `plan/checklist.md` |
| plan-check round 2 | PASS, signed marker | `_internal/plan_reviews/round_2.md` |
| code-execute first attempt | FAIL | `dev_logs/execute.md`; 744 tests, 19 failures, 2 errors |
| checked cross-harness execute fallback | dead/no transcript | exact attempt reconciled and harvested; partial test migrations retained and audited |
| single execute correction | in-scope Fleet gates green; returned FAIL on pre-existing boundary drift | `dev_logs/execute.md` |
| execute finalizer | PASS, signed marker | focused 20/20, Fleet 766/766, mirror parity; exact pre-existing boundary warning |
| independent cross-harness implementation review (round 1) | FAIL — 2 major findings | `_internal/dev_reviews/phase_review.md` |
| execute correction cycle | applied at the source | `dev_logs/execute_fix2_finalized.md`, `dev_logs/execute_fix2_review_correction.md` |
| root sequential adaptation boundary adjudication | PASS — prior concurrent boundary FAIL is a concurrency false negative, not a source defect | `_internal/dev_reviews/root_sequential_boundary_recheck.md` |
| independent cross-harness implementation review (final) | **PASS** | `_internal/dev_reviews/phase_review_final.md`, `att-bfc97217b160456cbb223809b2927bf7` |
| code-test (final) | **PASS**, 5/5 verification levels | `test_logs/verification_final.md`, `att-82f40fd6e38e4fb3bc6e5c18cde382b7` |
| code-report | this artifact | `pipeline_summary.md`, `final_report.md` |

## Resolved review findings (round 1 → fixed and re-verified)

The round-1 independent review (`_internal/dev_reviews/phase_review.md`) found
two major, reproducible F-36/F-37 defects. Both are now fixed at the source
and independently re-confirmed by the fresh final review
(`_internal/dev_reviews/phase_review_final.md`), not merely re-asserted:

1. **Process-view row order.** `_route_card()`/`_degrade_card()` previously
   built job/subagent lines first and appended context detail rows after,
   producing `job, subagents, ctx` instead of the required
   `job, ctx, subagents`. Fixed: both cards now build
   `[job_row, ctx_row, *subagent_strip]` inline per chunk
   (`render.py:2156-2223,2275-2307`), with no post-hoc batching. Confirmed by
   code read and by this review's own live `--once --view process`
   reproduction against the real registry.
2. **Owner-route-conflict unreachable.** `projection.py` previously returned
   before child routes were consulted whenever explicit owner evidence was
   present, making the named `owner-route-conflict` ambiguity path
   unreachable for a true direct owner/child conflict. Fixed: direct
   owner/child conflict detection now runs at `projection.py:360-373` and is
   covered by `test_direct_owner_route_conflict_is_fail_closed`.

Additional round-1 warnings — real collectors setting `sequence`/
`source_head_sequence` from the same sample, `demo.py` not covering a
populated composed `WorkProjection`, and no old-key-only JSON consumer test —
are also closed: `demo.py` now defines a deterministic composed-DAG owner
(`demo.py:26-27,57-61,81-82,190-199`), and
`test_t1_18_populated_snapshot_old_key_only_consumer_is_unchanged`
(`test_f28_route.py:338-372`) pins the old-key-only JSON consumer
byte-for-byte.

The `WorkProjection.ambiguity`-as-single-optional-string-vs-`ambiguity[]`
deviation noted in round 1 was not reopened as a blocking finding by the final
review; no other unresolved deviation remains.

## Correction coverage — F-36 through F-39 (final state)

- **F-36 (main-session record-ordered progress/stage).** Owner/conductor
  `stage_label` aggregates every active sealed route node in record order
  (`projection.py:394-404`, `_active_stage_label` at `projection.py:151-163`);
  a generic single child displays its node ID, agreeing parallel children
  display `{claim-a,claim-b}`. Proven by a real `_build_lines` regression with
  reversed child input at 168/120/100/60
  (`test_f36_work_projection.py:20-57`).
- **Composed-DAG projection.** Sealed `survey -> {claim-a,claim-b} -> synth`
  fixture (`tests/fixtures/route/synth_composed_survey.json`) exercised by
  route, breadcrumb, and process-view tests; provider-disabled group/process
  smoke independently renders the composed owner and both child chunks in
  corrected row order.
- **F-39 title quota/governor.** `utilities/model-worker-governor.py`'s
  `CLASS_LIMITS["title"]` now equals Fleet's hard ceiling `4` (was `1`);
  `refresh_title.py`'s `run_worker()` unconditionally acquires the central
  governor around the provider call. Proven by parity assertion plus four
  successful/one rejected admission test.
- **F-39 OpenCode private live-WAL snapshot immutability.**
  `_opencode_snapshot()` copies only the DB plus existing WAL into a private
  tempdir, refuses on a present rollback journal, verifies before/after
  `(dev, ino, size, mode, mtime_ns, ctime_ns)` signatures for all four
  source-path suffixes, and opens only `mode=ro&cache=private` against the
  private snapshot, never the live source or SHM. Proven with a live WAL
  writer held open across the read plus full byte+signature equality
  assertions.

## Implemented source and evidence

The worktree contains the full canonical `tools/fleet/**` implementation plus
its byte-identical mirror under `adapters/claude/tools/fleet/**`, and the
shared `utilities/model-worker-governor.py` change. This includes the common
`WorkProjection` resolver, route diagnostics and arbitrary DAG metadata,
child identity/context association, additive JSON, corrected context-detail
row ordering, title quota/OpenCode plumbing, the composed sealed fixture, and
the full F-36 through F-39 focused test modules. All changes remain
uncommitted in the current worktree.

## Verification evidence (fresh, from the final review and final test stage)

- Focused F-36 through F-39 correction tests: **76/76 PASS**.
- Full Fleet suite: **781/781 PASS** (one pre-existing benign
  `ResourceWarning` at `test_f27_control.py:521`).
- Compose-on-demand suite: **9/9 PASS**.
- Canonical capability-route compiler suite: **30/30 PASS**.
- Sealed composed fixture verification: **PASS**.
- Group/process `--once`, public `--json`, JSON parsing: **PASS**, provider-free.
- Canonical and Claude-mirror compilation: **PASS**.
- Canonical-to-Claude mirror parity: **1/1 PASS**, plus
  `diff -rq tools/fleet/ adapters/claude/tools/fleet/ --exclude=__pycache__`
  empty.
- Graduated final verification: **5/5 levels PASS** (syntax, import, smoke,
  functional, integration/behavioral runtime) — `test_logs/verification_final.md`.
- Sequential adaptation guard then boundary, run independently twice
  (once by the final review, once by the final test stage) in one foreground
  `set -e` shell each time: **PASS** both times; before/after `git status`
  identical both times; `WARN: 130 concrete Claude/model references remain in
  portable areas` is the documented, non-failing warning.
- No live, default, or custom title-provider invocation occurred in any
  command run by the correction, review, or test stages.

## Superseded historical boundary FAIL — not a source defect

The earlier adaptation-boundary FAIL recorded in
`execute_fix2_review_correction.md` (missing baseline hashes for two hook
files and a byte-ceiling overage) was caused by running the negative-sentinel
`adaptation-guard.test.sh` concurrently with `check-adaptation-boundary.sh`:
the guard test intentionally and temporarily corrupts two baseline hashes and
grows `adapters/claude/CLAUDE.md` by one byte before restoring the tree, and
the concurrently-running boundary process read that in-flight mutation.
`_internal/dev_reviews/root_sequential_boundary_recheck.md` reproduced this
diagnosis by rerunning both gates sequentially in one shell with identical
before/after `git status`; the final review and final test stage each
independently reran the same sequential pair and confirmed PASS. No boundary-
owned source correction was or is required.

## Runtime and lifecycle warnings (final, non-blocking)

- One benign pre-existing `ResourceWarning` at `test_f27_control.py:521`.
- The documented, allowed 130-concrete-reference adaptation-boundary warning.
- The owner-side `.spec-grounding` read marker remains unavailable/read-only
  in every worker's environment this cycle even though the PRD read itself
  succeeded; this is a harness-side degradation, not a defect introduced by
  this task.
- Initial owner-side spec-read/write grounding could not persist its marker
  for the same reason; registered stage workers had the checked writable
  projection and performed guarded reads and writes. The PRD was read
  completely at every stage that needed it.
- The first checked cross-harness execute fallback died with an empty
  transcript; its exact attempt row was reconciled `dead-worker-no-transcript`,
  harvested, and its partial edits were audited by the subsequent correction
  worker.
- The round-1 independent Claude review emitted a fenced FAIL handoff without
  closing its row; the owner reconciled only that exact attempt as
  `dead-worker-fail` and harvested its durable review artifact.
- All waits used `utilities/dispatch-wait.sh` synchronously in-turn; no
  asynchronous monitor, wakeup, or detached completion promise was used.

No other red or yellow Fleet v16 obligation remains open.

## Remaining work — root-only, not performed by this cycle's report stage

This report stage performed no source edits, no test execution changes, no
commit, no push, no merge, and no cleanup. The following remain root-owned
only:

1. Inspect this final handoff (`pipeline_summary.md`, this `final_report.md`,
   and the underlying review/test artifacts).
2. Commit the validated Fleet v16 diff.
3. Push/merge as appropriate for this branch.
4. Perform integrated verification again if the root judges it required after
   commit/merge.
5. Run the guarded worktree-cleanup check, then apply cleanup only if that
   guarded check passes.

This report stage explicitly did **none** of the above five actions.
