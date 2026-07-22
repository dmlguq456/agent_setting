---
status: active
created: 2026-07-22
---

# Fleet v16 implementation checklist

This checklist is the execution/test handoff for PRD v16 F-36 through F-39. Check an item only after the named source change and its hermetic evidence both exist. Canonical Fleet files are edited first; the Claude mirror is synchronized only after canonical tests pass.

## Plan-review correction status

- [x] Specify owner/conductor route discovery through `session_id/parent_sid` and `slug/parent_slug`, with one validated route/hash or stable ambiguity.
- [x] Define route-exact `stage_label` as the selected exact assigned contract for that validated leaf, otherwise opaque `route_node`; forbid semantic pipeline inference.
- [x] Thread `artifact_root` into exact-cardinality stage lookup and define a separate QA-only artifact resolver.
- [x] Specify the OpenCode collector → scheduler → argv/CLI → read-only DB delta → typed sidecar cursor chain and its hermetic tests.
- [x] Assign process-view detail rows to live job identities through exact `(pid, proc_start)` lookup.
- [x] Make context sequence/freshness evidence concrete and add the superseded route/artifact/dispatch test migration list.

## Gate A — additive data contracts and projection authority

- [x] Add public `ContextProjection` and `WorkProjection` in `tools/fleet/model.py` with safe defaults; keep public context JSON exactly `{used_pct, band, source}`.
- [x] Add private/non-serialized `ContextEvidence` with selected/head sequence, observation/freshness times, and invalidity reason.
- [x] Add optional Session route/env evidence plus Session `context` and `work_projection`.
- [x] Add DispatchJob child `context`, `work_projection`, and association ambiguity without removing/changing old fields.
- [x] Keep private route-view backing data out of public entity serialization.
- [x] Add diagnostic route validation in `tools/fleet/route.py`; explicit failures normalize to `route-record-mismatch`.
- [x] Preserve `write_scope`, `unit`, `unit_choices`, `depends_on`, gate, level, state, and progress in validated views/public route JSON.
- [x] Add `tools/fleet/projection.py` as the only WorkProjection resolver.
- [x] Implement leaf evidence order: validated exact route → exact registry/env identity → exactly one same-harness realpath-cwd candidate → route-absent exact artifact.
- [x] Resolve Session owners only through `session_id == parent_sid` and DispatchJob owners only through `slug == parent_slug`; require one agreed validated route/hash.
- [x] Emit `multiple-owner-routes`/`owner-route-conflict` instead of selecting the first/newest child; preserve same-route parallel nodes.
- [x] Map route-exact `stage_label` to the exact validated leaf contract when present, else opaque `route_node`; never infer from unit/key/role/fixed stages.
- [x] Treat any nonempty explicit tuple as a hard bar to artifact fallback.
- [x] Emit stable ambiguity codes: `route-record-mismatch`, `multiple-leaf-candidates`, `multiple-child-cwd-candidates`, `multiple-artifact-plan-dirs`, `multiple-owner-routes`, `owner-route-conflict` (all six are evidenced by focused projection regressions).
- [x] Preserve all same-route parallel active siblings in `active_nodes`; do not call them ambiguous.
- [x] Make artifact fallback the realpath-deduplicated exact-cardinality union of registry `artifact_root` and cwd-local report roots; keep it stage-only and remove fuzzy token/mtime selection.
- [x] Normalize context bands with 70/85 thresholds and selected/head sequence plus injected-clock freshness, accepting newer compaction decreases.

## Gate B — collectors and single child association

- [x] Capture route/contract/unit evidence from the already-read process env in `collectors/procscan.py`.
- [x] Keep `(pid, proc_start)` as the strong identity; never use PID alone.
- [x] Stop calling `live_stage()` as an independent authority in `collectors/dispatch.py`.
- [x] Add separate `resolve_plan_qa_artifact(job)` fallback after argv/jobs.log QA; pass `artifact_root`, require one exact candidate, and return QA only.
- [x] Populate legacy `DispatchJob.stage` from `work_projection.stage_label` after projection.
- [x] Preserve raw jobs.log/env/attempt evidence and terminal route-node evidence.
- [x] Add per-harness context evidence: Claude transcript `(mtime_ns,event offset)`, Codex rollout `(mtime_ns,event offset)`, OpenCode DB `(time_updated,rowid)`.
- [x] Replace `_adopt_child_titles` with one association over all child sessions.
- [x] Exact association requires `(pid, proc_start)`; an exact mismatch does not fall through to cwd.
- [x] Cwd fallback requires one same-harness `realpath(cwd)` child; two candidates fail closed.
- [x] Copy title, fresh NOW, and context atomically from the selected child.
- [x] Prove parent context is never inherited by a dispatch child.
- [x] Attach one WorkProjection to every Session and DispatchJob, including `source=none`.
- [x] Apply fresh Fleet sidecar title/NOW precedence in OpenCode while retaining native title fallback.
- [x] Expose private typed transcript/OpenCode refresh sources; keep paths and cursors out of public JSON.
- [x] Expose exact-session OpenCode message input with fixed compatible-table/rowid ordering from a consistency-checked ephemeral private DB+WAL snapshot using URI `mode=ro&cache=private`; do not copy/open source SHM, persist a copy, or write source DB/WAL/SHM.

## Gate C — all surfaces consume one projection

- [x] Project the snapshot before group/process/plain/JSON surface selection in `fleet.py`.
- [x] Keep `--json` and `--once` outside the title scheduler path.
- [x] Serialize top-level `route` from attached validated projection backing data, not a second resolution pass.
- [x] Remove renderer route-file reads and first-child/first-route selection.
- [x] Render exact contract-or-node leaf labels and all owner/conductor parallel active nodes in record order.
- [x] Render composed fork/fan-in without `_PIPE_STAGES` on validated or explicit-invalid paths.
- [x] Keep fixed historic stage labels only for genuinely route-absent legacy/artifact projection.
- [x] Preserve process-view node unit/gate/scope/state/progress from the same projection.
- [x] Replace process `session_by_pid` with `session_by_identity[(pid,proc_start)]`; pass attached projections into route/degrade cards.
- [x] Update demo entities with deterministic route-linked projection/context data and prove provider-disabled group/process/JSON smoke.

## Gate D — one `ctx … [· NOW]` row

- [x] Remove wide primary-row context gauge.
- [x] Remove narrow inline context telemetry.
- [x] Remove stack context gauge line.
- [x] Replace `_summary_row` with one context-first detail-row helper.
- [x] Live context+NOW renders `ctx NN% <band> · NOW`.
- [x] Live context-only renders no separator.
- [x] Live NOW-only renders `ctx — · NOW`.
- [x] Live with neither renders `ctx —`.
- [x] Stale/dead renders no detail row even with cached values.
- [x] Emit after the complete identity card and before the sub-agent strip in group and plain views.
- [x] In process view, emit beneath each live active-node/degrade job and before its exact-session sub-agent strip; route headers get no detail row.
- [x] Use dispatch-depth inset matching the sub-agent ladder.
- [x] Reserve context token first; clip only NOW with display-cell/CJK-safe helpers.
- [x] Assert row width `<=` terminal width at wide@168, wide@120, narrow@100, stack@60.

## Gate E — context orthogonality

- [x] At 69%, 70%, and 85%, only `context.band` and rendered context styling/text change.
- [x] Route graph/node state remains byte-equivalent.
- [x] Intensity/depth/model role/effort remains byte-equivalent.
- [x] QA/reviewer/test/retry/gate/guard/definition-of-done evidence remains byte-equivalent.
- [x] A lower percentage with a newer valid source sequence is accepted.
- [x] Missing, stale/expired, malformed, cross-source, or selected-sequence-before-source-head telemetry becomes `unknown`.

## Gate F — title/NOW worker contract

- [x] Set concurrency default `3`, hard max `4`.
- [x] Set rolling starts default/hard max `4` per `60s`.
- [x] Preserve main/child debounce `600s`/`150s`.
- [x] Preserve one shared main/child/default/custom cross-process slot/start pool.
- [x] Preserve per-session lock, stale lease recovery, environment/state kill switches, and fail-closed lock contention.
- [x] Prove direct `run_worker()` cannot bypass slot/start limits.
- [x] Enforce TITLE 3-6 words and at most 40 characters.
- [x] Preserve default provider tool denial and shell-free custom argv.
- [x] Document custom wrapper no-tools enforcement as wrapper-owned.
- [x] Carry typed refresh source through collector, `schedule_sessions()`, and `maybe_spawn()`.
- [x] Add mutually exclusive worker CLI sources: `--transcript` or paired `--opencode-db`/`--opencode-session`; reject harness/source mismatch.
- [x] Add tolerant exact-session OpenCode `mode=ro` message delta parsing with fixed table precedence and `rowid ASC` cursor order.
- [x] Persist integer OpenCode cursor in the existing harness sidecar `offset` plus additive `cursor_kind`; reset on kind/table mismatch and preserve old sidecars.
- [x] Advance the cursor exactly once on empty, rejected-title, and successful-title paths; prove source DB/WAL/SHM bytes/write metadata do not change while the ephemeral private snapshot is discarded.
- [x] Include ordinary Claude/Codex/OpenCode conversational children after 150s.
- [x] Exclude mem/title workers, app-server, dead/stale, and transcript-less nonconversational internal rows.

## Gate G — acceptance tests

- [x] Add `tools/fleet/tests/test_f36_work_projection.py`.
- [x] Add sealed `tools/fleet/tests/fixtures/route/synth_composed_survey.json` for `survey -> {claim-a,claim-b} -> synth`.
- [x] Extend the Fleet v16 regression set for arbitrary composed nodes, scope, fork/fan-in, siblings, progress, and no `_PIPE_STAGES` on validated/invalid route paths.
- [x] Assert Session `session_id/parent_sid` and DispatchJob `slug/parent_slug` owner resolution, same-route sibling preservation, multiple-route/hash ambiguity, and direct-owner/child conflict.
- [x] Assert assigned-contract and opaque route-node label parity across projection-backed group/process/plain/JSON paths.
- [x] Add `tools/fleet/tests/test_f37_context_detail.py`.
- [x] Add `tools/fleet/tests/test_f38_context_orthogonality.py`.
- [x] Update superseded context/subtitle/title-association assertions in `test_f16_f17_subtitle.py`, `test_dispatch_child_titles.py`, and `test_wide_ctx_gauge.py`.
- [x] Update `test_f30_gate_passed.py` explicit-invalid heuristic assertion, `test_f15_rows.py` live-stage/artifact-root assertions, and `test_dispatch.py` conductor/stage derivation assertions.
- [x] Search all Fleet tests for `live_stage`, `_find_plan_dir`, `source="heuristic"`, `_PIPE_STAGES`, and PID-only process lookup; superseded renderer assertions are migrated, while bounded route-absent legacy compatibility references remain intentional.
- [x] Add source-only unique `artifact_root`, cross-root duplicate cardinality, and separate QA-only artifact-resolution tests.
- [x] Add process-view context+NOW/context-only/NOW-only/unknown/stale/dead and `(pid,proc_start)` mismatch coverage at the approved widths.
- [x] Add selected/head sequence and freshness resolver coverage for the three harness contracts; assert private evidence is absent from JSON (collector source/head equality is bounded and documented).
- [x] Add `tools/fleet/tests/test_f39_title_quota.py` with fake clock, isolated state root, and 200-session backlog.
- [x] Extend title/provider regressions for OpenCode, 3/4, 4/60, 600/150, and 3-6-word validation.
- [x] Add temporary OpenCode DB exact-session delta and zero-write coverage.
- [x] Keep provider-disabled snapshot/demo/width/projection/storm paths fail-closed against provider starts.
- [x] Add old-key-only JSON consumer and additive `work_projection`/child-context assertions.
- [x] Keep all unrelated Fleet regressions passing (773/773).

## Gate H — canonical verification

- [x] Full Fleet suite passes:

  ```bash
  /home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh verification-runner --timeout 360 -- \
    env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/fleet/tests -p 'test_*.py'
  ```

- [x] Compose-on-demand suite passes:

  ```bash
  /home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh verification-runner --timeout 180 -- \
    env PYTHONDONTWRITEBYTECODE=1 python3 utilities/compose_route.test.py
  ```

- [x] Canonical route compiler suite passes:

  ```bash
  /home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- \
    env PYTHONDONTWRITEBYTECODE=1 python3 utilities/capability_route.test.py
  ```

- [x] Group once smoke passes without provider scheduling:

  ```bash
  env PYTHONDONTWRITEBYTECODE=1 FLEET_TITLE_DISABLE=1 FLEET_DEMO=1 AGENT_DISPATCH_JOBS=/dev/null \
    python3 tools/fleet/fleet.py --once --view group
  ```

- [x] Process once smoke passes without provider scheduling:

  ```bash
  env PYTHONDONTWRITEBYTECODE=1 FLEET_TITLE_DISABLE=1 FLEET_DEMO=1 AGENT_DISPATCH_JOBS=/dev/null \
    python3 tools/fleet/fleet.py --once --view process
  ```

- [x] Public JSON parses and old-key consumer passes:

  ```bash
  env PYTHONDONTWRITEBYTECODE=1 FLEET_TITLE_DISABLE=1 FLEET_DEMO=1 AGENT_DISPATCH_JOBS=/dev/null \
    python3 tools/fleet/fleet.py --json | python3 -m json.tool >/dev/null
  ```

- [x] Canonical Fleet bytecode compilation passes:

  ```bash
  env PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q tools/fleet
  ```

## Gate I — mirror and adaptation

- [x] Synchronize only after canonical pass:

  ```bash
  rsync -a --delete --exclude='__pycache__' tools/fleet/ adapters/claude/tools/fleet/
  ```

- [x] Canonical and mirror compile:

  ```bash
  env PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q tools/fleet adapters/claude/tools/fleet
  ```

- [x] Mirror parity passes:

  ```bash
  env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tools.fleet.tests.test_mirror_parity
  ```

- [x] Adaptation guard regression passes:

  ```bash
  bash tools/adaptation-guard.test.sh
  ```

- [x] Full adaptation boundary passes (exit 0; 127 documented adapter-mapping warnings remain non-task-owned):

  ```bash
  bash tools/check-adaptation-boundary.sh
  ```

## Gate J — report and QA assurance

> Execution evidence is recorded in `dev_logs/execute.md`. Fleet/compose/compiler/mirror gates pass; the full adaptation boundary remains unchecked because two unrelated delta-baseline rows have `field 4='-'`.

- [x] Record every changed canonical and mirror file.
- [x] Record each command, result, pass count, and warning in the canonical code-cycle artifacts.
- [x] Map the task-owned PRD §4.12 acceptance rows to passing focused/full tests.
- [x] Record the provider-disabled zero-call boundary.
- [x] Record that compose/compiler behavior was verified but not duplicated in Fleet.
- [x] Record group/process once, JSON, syntax compile, mirror, and adaptation results.
- [x] Record the known owner-side spec-read-marker degradation: PRD read succeeded; `.spec-grounding` marker side effect was unavailable/read-only.
- [x] Complete and report standard code QA assurance exactly as `plan-check:selected-independent-pass:final-verify`.
- [ ] Do not claim completion until the independent selected pass and final verification both succeed.

## Plan-stage completion evidence

- [x] Canonical PRD v16 read, especially F-36 through F-39 and the §4.12 acceptance matrix.
- [x] Approved Fleet research handoff and final specification verdict read.
- [x] Actual Fleet model/collectors/route/render/fleet/title source and relevant tests inspected.
- [x] Compose-on-demand implementation and tests at `e8938809` inspected; current Fleet/compose source is unchanged since that commit.
- [x] File-level ownership and dependency order recorded.
- [x] Complete acceptance matrix translated into implementation and test tasks.
- [x] Concrete Fleet/compose/compile/once/JSON/mirror/adaptation commands recorded.
- [x] Standard QA assurance and spec-read-marker degradation recorded.
- [x] Durable plan/checklist paths are under the canonical artifact root.
- [x] Merged review round 1 corrections applied in place with plan change history; no implementation item was marked complete.

## Correction-cycle evidence — 2026-07-22 (attempt att-0018128bffc840b593304e17006d3c5a)

- [x] Owner/main projection labels aggregate every active sealed node in record order; generic `autopilot-code` child contracts cannot hide sibling IDs.
- [x] Real Session `_build_lines` regressions cover reversed child input at 168/120/100/60 and single-generic-child/parallel-owner labels.
- [x] `synth_composed_survey.json` is exercised by route, breadcrumb, and process-view tests; provider-disabled group/process smoke exercises the composed owner and route/degrade chunks.
- [x] Populated `_snapshot_json()` old-key-only consumer coverage preserves `model`, `harness`, `effort`, `elapsed_min`, and `note`; private evidence/backing data remain absent.
- [x] F-39 title test isolation and central governor title ceiling 4 are covered; live-WAL private DB+WAL snapshot preserves source DB/WAL/SHM/journal bytes and metadata.
- [x] Canonical-to-Claude mirror parity, Fleet 781/781, compose 9/9, capability-route 30/30, fixture verify, provider-disabled smoke, compileall, diff-check, and adaptation guard passed.
- [ ] Final adaptation boundary remains red on two pre-existing missing unrelated baseline hashes and the known Claude bootstrap byte ceiling; completion marker was not bound.
