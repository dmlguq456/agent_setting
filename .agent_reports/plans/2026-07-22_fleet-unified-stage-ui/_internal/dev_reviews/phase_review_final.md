# Fleet v16 independent implementation review — final

## Verdict

**PASS.** No substantive red or yellow Fleet v16 obligation remains. The
review-correction cycle's one prior finding (owner/conductor `stage_label`
first-child selection) is genuinely fixed at the source, is covered by a real
`_build_lines` render regression (not just a data-layer assertion), and every
previously-noted proof gap (composed-DAG render coverage, demo fixture,
old-key-only JSON consumer, F-39 hermetic isolation, live-WAL source
immutability, central governor alignment) is closed with fresh, independently
reproduced evidence. `plan-check:selected-independent-pass:final-verify` may
advance to `test`.

## Scope and method

Read completely: `core/CORE.md`, `core/WORKFLOW.md`, `core/CONVENTIONS.md`,
`core/OPERATIONS.md`, the full v16 PRD (`spec/agent-fleet-dashboard/prd.md`,
§4.12 F-36..F-39 + acceptance matrix + the surrounding F-14..F-35 context that
those sections build on), `plan/plan.md`, `plan/checklist.md`,
`phase_review_followup.md` (prior FAIL — 1 major, 3 yellow),
`orchestrator_repro.md` (8 must-fix, independently confirmed by
`phase_review_followup.md`), `root_post_execute_findings.md` (4 open items),
`execute_fix2_review_correction.md` (the correction worker's own claims),
`root_sequential_boundary_recheck.md` (the guard/boundary concurrency
false-negative adjudication), and `owner_handoff_followup.md` (superseded
historical context — attempt history only, not treated as current evidence).

Adopted a refute-by-default stance: read `tools/fleet/projection.py`,
`tools/fleet/model.py`, and `tools/fleet/route.py` in full; read the specific
`render.py`, `collectors/__init__.py`, `refresh_title.py`,
`utilities/model-worker-governor.py`, and `demo.py` regions the correction
touched; ran every command in the assignment's nine correction groups fresh
against the current worktree (not the prior workers' logs); and independently
reproduced the two live-output scenarios (`--once --view group`/`process`,
both demo and real-registry `AGENT_DISPATCH_JOBS`) rather than trusting green
test counts alone, per the prior review's own stated method.

## Correction-group evidence (1–9)

1. **Main `Session` single-node and record-ordered parallel stage/progress at
   168/120/100/60, generic child-contract masking, reversed child input, all
   sibling IDs visible, explicit/ambiguous evidence failing closed with no
   fixed/first-route fallback.** ✅ Confirmed at the source. The prior FAIL's
   Major Finding A (`projection.py:376-385`, `p = exact[0]` copying one
   arbitrary child's own single-node `stage_label` onto the owner) is fixed:
   the owner-aggregation branch (`resolve_work_projection`,
   `tools/fleet/projection.py:394-404`) now derives the owner's
   `stage_label` from `_active_stage_label(active)` (`projection.py:151-163`),
   which formats **every** active node id in sealed record order
   (`{claim-a,claim-b}`) rather than one child's own label — and `active` is
   the full-route active-node list computed by `_record_view` over *all* jobs
   sharing that `route_id` (not just the arbitrarily-first child), so the
   result is independent of collector/jobs iteration order by construction,
   not by accident.
   - `test_session_owner_render_shows_all_parallel_siblings_in_sealed_order`
     (`test_f36_work_projection.py:20-57`) is a real `render._build_lines`
     regression — not a data-layer-only assertion — that deliberately
     constructs the two `DispatchJob` children in **reversed** order
     (`claim-b` before `claim-a`), attaches projections, and asserts at
     168/120/100/60 that the rendered text contains `claim-a`, `claim-b`,
     `{claim-a,claim-b}`, and explicitly `assertNotIn("stage autopilot-code",
     text)` — this is exactly the scenario the prior review's reproduction
     showed broken (`claim-b never appears anywhere on the owner's own row`).
   - `test_owner_stage_label_uses_node_ids_for_generic_single_and_parallel_children`
     (`test_f36_work_projection.py:59-81`) separately pins the single-active
     case (`stage_label == "execute"`, the node id, not the generic
     `autopilot-code` contract) and the parallel case
     (`stage_label == "{claim-a,claim-b}"`).
   - Live-reproduced independently in this review via both
     `FLEET_DEMO=1 --once --view group` (`demo-composed-owner ... stage
     {claim-a,claim-b} 1/4`) and `--once --view process`
     (`rt-63788ad6 — 1/4 nodes`, both `claim-a`/`claim-b` chunks with their own
     `ctx` rows).
   - Explicit-invalid/ambiguous fail-closed with no fixed/first-route
     fallback: `_dispatch_stage_segs` (`render.py:839-844`) returns `[]`
     immediately whenever `projection.ambiguity` is set, before any
     `_PIPE_STAGES`/`route_seq` breadcrumb logic runs — an ambiguous
     projection can never fall through to a guessed pipeline. Confirmed by
     code read; `source="registry-exact"` is only ever produced with a
     non-`None` `ambiguity` (`_candidate_projection`,
     `projection.py:294-300`, and the explicit-tuple branch,
     `projection.py:374-382`), so "record present but unresolved" and
     "explicit tuple but no record" both always carry ambiguity and never
     reach a fixed-breadcrumb path. `_PIPE_STAGES`/`_stage_segs` without
     `route_seq` is reachable only for genuinely route-absent
     (`source="none"`, no ambiguity) and `artifact-inferred` rows — matching
     F-36c/F-36d/F-28b's "legacy fallback only when tuple is completely
     absent" requirement, verified by direct code trace, not inference from
     the checklist.

2. **Exact `(pid,proc_start)` and unique same-harness realpath-cwd
   association; PID reuse, duplicate PID/cwd, cross-harness, attempt-only
   owner traversal, direct owner/child conflict.** ✅ Confirmed correct and
   unchanged from the already-verified prior pass
   (`projection.py:317-343` for the leaf join, `projection.py:268-273` for
   the attempt-is-not-a-route-tuple exclusion, `projection.py:276-286` for
   `session_id/parent_sid` and `slug/parent_slug` owner-link traversal,
   `projection.py:360-373` for direct owner/child conflict detection). All
   still covered and green:
   `test_unique_exact_and_unique_cwd_candidates_are_adopted`,
   `test_pid_reuse_and_duplicate_cwd_candidates_refuse_adoption`,
   `test_attempt_only_and_both_owner_link_contracts_traverse_children`,
   `test_direct_owner_route_conflict_is_fail_closed`. Child-level
   title/NOW/context association (`collectors/__init__.py:63-101`,
   `_adopt_child_titles`) independently re-read: exact identity present ⇒
   cwd is never consulted even on zero exact candidates (no fallback after an
   exact-identity attempt); cwd fallback only fires when no job-side identity
   tuple exists at all; both source and no-source paths never mix
   title/NOW/context from different children. Covered by
   `test_exact_identity_copies_title_now_and_context_atomically`,
   `test_pid_reuse_cwd_ambiguity_and_cross_harness_are_fail_closed`,
   `test_parent_context_is_not_inherited` (`test_f37_context_detail.py`).

3. **Process-view per-entity order: job identity → exactly one
   `ctx ... [· NOW]` line → exact-session subagent strip, across route/degrade
   and live/missing/stale/dead at the approved widths.** ✅ Confirmed via
   code (`_route_card`/`_degrade_card`, `render.py:2156-2223,2275-2307` build
   `[job_row, ctx_row, *subagent_strip]` per chunk inline, no post-hoc
   batching) and live-reproduced independently in this review's own
   `--once --view process` output against the real registry: this worker's
   own row rendered as `└▸🚀 fleet-unified-stage-ui-final-review-v3 ...` →
   `ctx —` with no extraneous batching. `test_process_route_chunk_orders_job_context_then_exact_session_subagents`
   (`test_f37_context_detail.py:110+`) and the width/degrade/stale/dead
   fixtures in `test_f30_process_view.py`/`test_f37_context_detail.py` pin
   this at the approved widths.

4. **Sealed `survey -> {claim-a,claim-b} -> synth` through route
   verification, normalized projection, record-order levels/parallel/fan-in,
   breadcrumb, group, process, provider-disabled demo, progress,
   unit/gate/write-scope, and populated old-key-only `_snapshot_json()`
   consumer; no fixed stage vocabulary on sealed or explicit-invalid paths.**
   ✅ All proof gaps the prior review named are closed:
   - `grep -rln "synth_composed_survey\|claim-a" tools/fleet/tests/*.py` now
     matches `test_f28_route.py`, `test_f28_breadcrumb.py`, and
     `test_f30_process_view.py` (previously matched none) — record order,
     `write_scope`, breadcrumb text
     (`survey › claim-a › claim-b › synth`), and process-card node labels
     (`claim-a[research/claim-verify]`, `claim-b[research/claim-verify]`) are
     each independently asserted.
   - `demo.py` now defines a `demo-composed-owner` Session with two
     `demo-composed-claim-a`/`-b` children on the sealed route
     (`demo.py:26-27,57-61,81-82,190-199`); provider-disabled
     `--once --view group` visibly renders `stage {claim-a,claim-b} 1/4` on
     the owner's own primary row, and `--once --view process` renders both
     child chunks with their own `ctx` rows — independently reproduced in
     this review, not merely read from a log.
   - `test_t1_18_populated_snapshot_old_key_only_consumer_is_unchanged`
     (`test_f28_route.py:338-372`) is a dedicated test that builds a
     populated `Session`+`DispatchJob` pair, runs the full
     `fleet._snapshot_json()` pipeline (not `route_summary_from_projections()`
     directly), narrows to exactly the four legacy top-level keys, asserts
     `model/harness/effort/elapsed_min/note` byte-identical values on a route
     node, and asserts `_context_evidence`/`_route_view` are absent anywhere
     in the serialized JSON — closing the "not really a dedicated test" gap
     the prior review flagged.
   - `_PIPE_STAGES`/fixed-pipeline absence on sealed and explicit-invalid
     paths independently re-verified by code trace (see group 1's fail-closed
     analysis) rather than re-trusting the test suite alone.

5. **Public JSON is additive and preserves populated old meanings/keys.** ✅
   Confirmed both by code (`route_summary_from_projections`,
   `projection.py:446-486`, builds directly from the attached
   `projection._route_view`, never reopens a route file) and by this review's
   own fresh `--json | python3 -m json.tool` run against both demo and the
   real registry: legacy node keys `model`, `harness`, `effort`,
   `elapsed_min`, `note` present with correct values; `work_projection` and
   child `context` present and additive; no `_context_evidence`/`_route_view`
   leakage anywhere in the serialized output (spot-checked directly, not only
   via the passing test).

6. **Title/NOW quota effective, not only locally configured.** ✅ All four
   `root_post_execute_findings.md` items independently re-verified as fixed:
   - Item 1 (F-39 hermetic isolation): `test_f39_title_quota.py:23,27`
     isolates `AGENT_MODEL_GOVERNOR_ROOT` under the test tempdir in `setUp`
     and restores it in `tearDown`, so the exact-provider-call-count test no
     longer double-counts `model-worker-governor.default_root()`'s own
     `subprocess.run` against `utilities/artifact-root.sh`.
   - Item 2 (effective concurrency capped at 1 by the shared governor):
     `utilities/model-worker-governor.py:18` now reads
     `CLASS_LIMITS = {"dispatch": 3, "distill": 1, "title": 4, "loop": 2}`
     (previously `"title": 1`), and `refresh_title.py:609-657`'s
     `run_worker()` unconditionally acquires the central governor
     (`governor_module.acquire(governor_root, "title")`) around the actual
     provider `subprocess.run` call, in addition to Fleet's own local
     slot/start leases — so both layers now agree at 4, and no path can
     cross the provider boundary while holding only the (now-redundant)
     local lease.
     `test_title_class_admits_four_and_rejects_fifth_with_fleet_ceiling`
     (`test_f39_title_quota.py:159-174`) is a genuine combined-admission
     regression: it asserts `governor.CLASS_LIMITS["title"] ==
     rt.MAX_CONCURRENCY` (parity, not a hand-duplicated constant) and proves
     4 real governor acquisitions succeed while a 5th raises.
   - Item 3 (main-session stage label naming the generic contract instead of
     the active node): this is the same defect as, and fixed by, the group 1
     owner-aggregation correction — re-verified live in this review via the
     real registry's `--once --view process` output showing
     `impl-review[qa/code-review] ●` as the active node (not a generic
     `autopilot-code` contract label).
   - Direct `run_worker()` bypass: `test_direct_worker_uses_same_start_budget_and_provider_is_not_reached_after_limit`
     (`test_f39_title_quota.py:78-88`) proves a second direct call is refused
     once the local budget is exhausted, and `run_worker()`'s code path
     (above) proves the central governor is acquired unconditionally on the
     path that is exercised — a direct call cannot skip either guard.

7. **OpenCode private live-WAL snapshot sees an uncheckpointed exact-session
   row while source DB/WAL/SHM/journal bytes and write metadata remain
   unchanged.** ✅ `root_post_execute_findings.md` item 4 (URI `mode=ro`
   alone still mutates the live `-shm` file) is fixed by
   `_opencode_snapshot()` (`refresh_title.py:259-284`): it copies only the
   database and an already-present WAL into a private tempdir (reflink
   preferred, streaming fallback, `refresh_title.py:232-256`), refuses to
   proceed if a rollback journal is present, verifies before/after
   `(dev, ino, size, mode, mtime_ns, ctime_ns)` signatures for all four
   source-path suffixes are identical, and only ever opens
   `mode=ro&cache=private` against the **private snapshot** path, never the
   live source — the SHM is never opened or copied at all.
   `test_live_wal_snapshot_reads_exact_row_without_source_mutation`
   (`test_f39_title_quota.py:114-156`) keeps a real WAL writer open with an
   uncheckpointed row across the read, asserts the uncheckpointed data is
   visible (`("uncheckpointed", "message")`), and asserts full byte+signature
   equality for `db`, `db-wal`, `db-shm`, and `db-journal` before/after. This
   is a stronger and more literal proof than the review's own assignment
   text asks for.

8. **Compose-on-demand compiler and capability-route compatibility.** ✅
   Unchanged and out of this task's edit scope, confirmed by fresh reruns
   (`utilities/compose_route.test.py` 9/9, `utilities/capability_route.test.py`
   30/30, both PASS in this review) and by code read: `route.py` and
   `projection.py` only read `unit_catalog_digest`/`composed`/node
   `unit`/`unit_choices` from an already-sealed record; neither module
   imports or calls the compose compiler. No Fleet recompile of the unit
   catalog anywhere in the diff.

9. **No live/default/custom provider invocation in any test/snapshot/demo
   path; canonical-to-Claude mirror parity; full suite; adaptation guard and
   boundary strictly sequential.** ✅ All fresh in this review, not read from
   a prior log:
   - `python3 -m unittest discover -s tools/fleet/tests -p 'test_*.py'` →
     **781/781 PASS** (one pre-existing benign `ResourceWarning`, not a
     failure).
   - `python3 utilities/compose_route.test.py` → **9/9 PASS**.
   - `python3 utilities/capability_route.test.py` → **30/30 PASS**.
   - `FLEET_TITLE_DISABLE=1 FLEET_DEMO=1 AGENT_DISPATCH_JOBS=/dev/null
     fleet.py --once --view group` → exit 0, composed owner row visible.
   - `FLEET_TITLE_DISABLE=1 FLEET_DEMO=1 AGENT_DISPATCH_JOBS=/dev/null
     fleet.py --once --view process` → exit 0, per-chunk `ctx` rows in order.
   - `--json | python3 -m json.tool` → exit 0, parses, additive keys
     confirmed.
   - `python3 -m compileall -q tools/fleet adapters/claude/tools/fleet` →
     PASS.
   - `python3 -m unittest tools.fleet.tests.test_mirror_parity` → PASS.
   - `diff -rq tools/fleet/ adapters/claude/tools/fleet/ --exclude=__pycache__`
     → empty (byte parity).
   - `git diff --check` → exit 0.
   - **Sequential adaptation guard/boundary** (run twice independently in
     this review, once as part of a background job and once again standalone
     in the foreground with `git status` captured immediately before and
     after both commands): `bash tools/adaptation-guard.test.sh` → PASS, all
     9 negative sentinel cases; `bash tools/check-adaptation-boundary.sh` →
     `WARN: 130 concrete Claude/model references...` (documented
     adapter-mapping warning) then `OK: adaptation boundary checks passed`,
     exit 0; git status identical before and after. One earlier read of an
     in-flight background log transiently showed a boundary FAIL
     (`__pycache__` under `adapters/codex/bin`/`adapters/opencode/bin` plus a
     capability-info complaint) — this was caught while an orphaned
     verification-runner subprocess from this review's own earlier
     timed-out (3-minute) foreground attempt was still finishing in the
     background, i.e. the same class of transient concurrent-process
     interference `root_sequential_boundary_recheck.md` already diagnosed,
     not a code defect. No stray adaptation-related process was found running
     (`ps -ef` clean) before the final confirmation run, and `git diff
     --check` plus `tools/adaptation-exemptions.tsv`'s two delta-row hashes
     (`d07c732c...`, `d42789a2...`) and `adapters/claude/CLAUDE.md`'s size
     (5,614 bytes, under the 16,384 ceiling) were independently spot-checked
     clean in the current worktree, matching the two prior runs' PASS
     verdicts.

   No live/default/custom title provider was invoked by any command above or
   by this review itself; the hermetic fail-if-reached provider guards inside
   the 781-test count are part of this evidence, not the whole of it.

## Full command/result table (this review's own fresh runs)

| Command | Result |
|---|---|
| `python3 -m unittest discover -s tools/fleet/tests -p 'test_*.py'` | PASS, 781/781 |
| `python3 utilities/compose_route.test.py` | PASS, 9/9 |
| `python3 utilities/capability_route.test.py` | PASS, 30/30 |
| `FLEET_DEMO=1 --once --view group` | exit 0; `demo-composed-owner ... stage {claim-a,claim-b} 1/4` visible |
| `FLEET_DEMO=1 --once --view process` | exit 0; per-job `ctx` rows in correct order, composed DAG card correct |
| Real-registry `--once --view group/process` (`AGENT_DISPATCH_JOBS` unset from `/dev/null`) | exit 0; this worker's own `impl-review` node visible as the active node, not a generic contract label |
| `--json \| python3 -m json.tool` | exit 0, parses; legacy node keys + additive `work_projection`/`context` confirmed by direct inspection |
| `python3 -m compileall -q tools/fleet adapters/claude/tools/fleet` | PASS |
| `python3 -m unittest tools.fleet.tests.test_mirror_parity` | PASS, 1/1 |
| `diff -rq tools/fleet/ adapters/claude/tools/fleet/ --exclude=__pycache__` | empty (byte parity) |
| `git diff --check` | exit 0 |
| `bash tools/adaptation-guard.test.sh` (sequential, standalone) | PASS, 9/9 negative sentinel cases |
| `bash tools/check-adaptation-boundary.sh` (sequential, standalone, immediately after guard) | exit 0; `WARN: 130 concrete Claude/model references...`; `OK: adaptation boundary checks passed` |
| `git status` before vs. after the sequential guard+boundary pair | identical (empty diff) |

## No-live-provider statement

Zero live/default/custom title-provider invocations occurred in any command
run by this review or by the suites it executed. `refresh_title.py`'s
`run_worker()` and `maybe_spawn()` fail-if-reached guards, exercised inside
the 781-test discovery run, are part of this evidence; this review additionally
ran the CLI/demo/JSON smokes itself with `FLEET_TITLE_DISABLE=1` as defense in
depth, consistent with the plan's stated contract that `--once`/`--json` never
enter the scheduler regardless of that flag.

## Mirror parity

`diff -rq` empty, `test_mirror_parity` PASS, and both canonical and mirror
trees compile — all independently rerun in this review, not read from a log.

## Other observations (not blocking)

- The `Fleet title work/.runtime/model-worker-governor/{lock,state.json}`
  stray directory noted in `phase_review_followup.md` was not present in this
  review's worktree at the time of inspection; no action needed.
- The layout-cutoff terminology note in `phase_review_followup.md` (PRD §3's
  "70/110 컷오프" vs. the real `_NARROW_CUTOFF=70`/`_TWO_LINE_CUTOFF=138`
  constants) is pre-existing doc/code drift unrelated to this task; not
  reproduced as a new issue and not a completion blocker.
- The already-disclosed owner-side `.spec-grounding` marker degradation
  (PRD read succeeded; the Codex spec-read marker write is read-only in this
  worker environment) is consistent with every prior worker's disclosure and
  is not a defect introduced by this change.

## Required assurance

Standard code QA assurance `plan-check:selected-independent-pass:final-verify`
is met by this review. No major or yellow Fleet v16 obligation remains open.

## Recommendation

`plan-check:selected-independent-pass:final-verify` may advance to `test`
(and, on `test` PASS, `report`). No further correction cycle is needed for
Fleet v16 F-36 through F-39.
