# Fleet v16 unified stage/context UI — pipeline summary (final continuation)

## Verdict

**PASS.** The fresh independent cross-harness implementation review
(`att-bfc97217b160456cbb223809b2927bf7`, `_internal/dev_reviews/phase_review_final.md`)
and the final verification stage (`att-82f40fd6e38e4fb3bc6e5c18cde382b7`,
`test_logs/verification_final.md`) both returned PASS. No red or yellow Fleet
v16 (F-36 through F-39) obligation remains open.

## Route identity

- Route: `rt-dfec3aabe921b37f`
- Route hash: `sha256:dfec3aabe921b37fa9da8973c530b48ea92b7a9cd8fa9cdff7a7dd950512d404`
- Capability/mode/intensity/QA: `autopilot-code` / `dev/refactor` / strong /
  `plan-check:selected-independent-pass:final-verify`
- Pipeline: `code-plan -> code-execute -> code-test -> code-report`, with an
  independent implementation review inserted before `code-test`.

## What changed in this final continuation

The prior owner report (`final_report.md`, previous cycle) recorded a FAIL at
`impl-review`: two major F-36/F-37 defects (process-view row order batching
context after subagents instead of before, and an unreachable
`owner-route-conflict` path for a direct owner/child route conflict). Both
were corrected at the source and re-reviewed fresh, independently, from the
current worktree — not by re-trusting the prior workers' logs:

- **Fresh independent review** (`_internal/dev_reviews/phase_review_final.md`,
  `att-bfc97217b160456cbb223809b2927bf7`): PASS. Confirms both prior findings
  fixed at the source, backed by real `render._build_lines` regressions (not
  data-layer-only assertions), and closes every previously-noted proof gap
  (composed-DAG render coverage, demo fixture, old-key-only JSON consumer,
  F-39 hermetic isolation, live-WAL source immutability, central governor
  alignment) with fresh, independently reproduced evidence.
- **Final test stage** (`test_logs/verification_final.md`,
  `att-82f40fd6e38e4fb3bc6e5c18cde382b7`): PASS at all 5 graduated
  verification levels (syntax, import, smoke, functional, integration/
  behavioral runtime).

## Fresh evidence (independently rerun by both the review and the test stage)

- Fleet suite: **781/781 PASS**.
- Compose-on-demand suite: **9/9 PASS**.
- Canonical capability-route compiler suite: **30/30 PASS**.
- Canonical-to-Claude mirror parity: **1/1 PASS** (`test_mirror_parity`), plus
  `diff -rq tools/fleet/ adapters/claude/tools/fleet/ --exclude=__pycache__`
  empty (byte-identical).
- Graduated verification: **5/5 levels PASS** (syntax/compileall, import,
  smoke, functional/unit, integration-behavioral runtime).
- Provider-disabled `--once --view group`, `--once --view process`, and
  `--json | python3 -m json.tool` smokes: all exit 0, composed owner/process
  cards render correctly, additive JSON keys confirmed. **No live, default,
  or custom title-provider call occurred** in any command run by either
  stage; the hermetic fail-if-reached provider guards inside the 781-test
  count are corroborating evidence, not the sole evidence.

## Sequential adaptation guard/boundary

Run twice independently (once by the fresh review, once by the fresh test
stage), each time in one foreground `set -e` shell with no background
process, job control, timeout orphan, parallel runner, or overlap:

```sh
git status --porcelain=v1 > BEFORE
bash tools/adaptation-guard.test.sh
bash tools/check-adaptation-boundary.sh
git status --porcelain=v1 > AFTER
diff -u BEFORE AFTER
```

Both runs: `adaptation-guard.test.sh` PASS (all 9 negative sentinel cases);
`check-adaptation-boundary.sh` exit 0 with the documented
`WARN: 130 concrete Claude/model references remain in portable areas` followed
by `OK: adaptation boundary checks passed`; before/after `git status` snapshots
identical (empty diff) both times.

The earlier concurrent adaptation-boundary FAIL recorded in
`execute_fix2_review_correction.md` is **not a source defect**. Per
`_internal/dev_reviews/root_sequential_boundary_recheck.md`, that worker ran
the negative-sentinel guard test (which intentionally corrupts two baseline
hashes and grows `adapters/claude/CLAUDE.md` by one byte, then restores the
tree) concurrently with the boundary checker; the boundary process read the
guard's transient in-flight mutation and reported exactly those three sentinel
failures as if they were real. Root's own sequential rerun, and both
subsequent independent sequential reruns in this final continuation, all PASS
with identical before/after `git status`, confirming the concurrency
false-negative diagnosis and that no boundary-owned source correction is
required.

## Correction coverage — F-36 through F-39

1. **Main-session record-ordered progress/stage (F-36).** Owner/conductor
   `stage_label` now derives from every active sealed route node in record
   order (`projection.py:394-404`, `_active_stage_label`,
   `projection.py:151-163`) instead of one arbitrarily-first child's own
   label. Covered by a real render regression
   (`test_session_owner_render_shows_all_parallel_siblings_in_sealed_order`,
   `test_f36_work_projection.py:20-57`) that deliberately reverses child order
   and asserts both sibling IDs and the sealed-order set label appear on the
   owner's own row.
2. **Composed-DAG projection (F-36/F-37).** The sealed
   `survey -> {claim-a,claim-b} -> synth` fixture
   (`tests/fixtures/route/synth_composed_survey.json`) is exercised by route,
   breadcrumb, and process-view tests; provider-disabled group/process smoke
   independently renders the composed owner (`stage {claim-a,claim-b} 1/4`)
   and both child chunks with per-job `ctx` rows in the corrected
   job-then-context-then-subagent order.
3. **Effective title quotas/governor (F-39).** `utilities/model-worker-governor.py`'s
   `title` class ceiling now matches Fleet's hard ceiling of 4
   (previously 1), and `refresh_title.py`'s `run_worker()` unconditionally
   acquires the central governor around the provider call in addition to
   Fleet's local lease, so both layers agree. Proven by a combined-admission
   regression asserting parity between `governor.CLASS_LIMITS["title"]` and
   Fleet's `MAX_CONCURRENCY`, four real acquisitions succeeding, and a fifth
   raising.
4. **OpenCode private live-WAL snapshot immutability (F-39).**
   `_opencode_snapshot()` copies only the database plus an already-present WAL
   into a private tempdir, refuses to proceed if a rollback journal is
   present, verifies before/after `(dev, ino, size, mode, mtime_ns, ctime_ns)`
   signatures for all four source-path suffixes, and only ever opens
   `mode=ro&cache=private` against the private snapshot — never the live
   source, and the SHM is never opened or copied. Proven by a test that keeps
   a real WAL writer open with an uncheckpointed row across the read, asserts
   the uncheckpointed data is visible, and asserts full byte+signature
   equality for `db`, `db-wal`, `db-shm`, and `db-journal` before/after.

## Warnings (non-blocking, disclosed only — no other findings)

- One benign pre-existing `ResourceWarning` at `test_f27_control.py:521` for
  an unclosed source file; the 781-test suite still completes green.
- The documented, allowed 130-concrete-reference adaptation-boundary warning
  (`WARN: 130 concrete Claude/model references remain in portable areas`) —
  explicitly non-failing.
- The owner-side `.spec-grounding` read marker remains unavailable/read-only
  in this worker environment even though the PRD read itself succeeded; this
  is a harness-side degradation disclosed by every prior worker in this cycle,
  not a defect introduced by this task.

No other red or yellow Fleet v16 obligation remains.

## Remaining work — root-only, not performed by this worker

This report stage performed no source edits, no test execution changes, no
commit, no push, no merge, and no cleanup. The following steps remain and are
root-owned only:

1. Inspect the full handoff (this `pipeline_summary.md`, the updated
   `final_report.md`, and the underlying review/test artifacts).
2. Commit the validated Fleet v16 diff.
3. Push/merge as appropriate for this branch.
4. Perform integrated verification again if the root judges it required after
   commit/merge.
5. Run the guarded worktree-cleanup check, then apply cleanup only if that
   guarded check passes.

This report stage explicitly did **none** of the above five actions.
