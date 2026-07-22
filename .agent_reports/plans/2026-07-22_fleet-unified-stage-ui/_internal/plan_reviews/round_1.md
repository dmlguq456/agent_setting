## 📋 Plan Review Results

**Target:** `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-unified-stage-ui/plan/plan.md` (with `checklist.md`)

**Plan summary:** The plan is directionally complete and tracks the approved v16 PASS specification: one projection, fail-closed evidence, arbitrary DAGs, unified child telemetry, all-layout detail rows, quota changes, hermetic tests, and mirror gates. The current source remains the v15 baseline, but several construction boundaries are underspecified enough that implementation could pass local unit tests while missing required behavior.

**Verdict:** 🔴 5 issues (5 major)

*(This file merges two independent review passes on the same plan/checklist — both grounded the plan against the canonical PRD, `verdict-final-4.json`, and live source at every cited file:line, and both found the plan unusually well-grounded factually. The five 🔴 items below are additive findings from the two passes, not duplicates — each was independently spot-checked against source before being kept.)*

## 🔴 Must-fix before execution

### plan step 1.3.5 / plan step 3.2.1 (group view) — owner/conductor route discovery mechanism is unspecified

**Current code state:** A depth-1 conductor (`DispatchJob` with `dispatch_depth=1`, or an interactive `Session` acting as capability owner) essentially never carries its own `route_id`/`route_node` today — `dispatch.py` attaches the env/pipe route link only to the depth-2 stage worker (`render.py:2897-2901`'s own comment: "the dispatch-depth-1 conductor row itself rarely carries route_id"). The only place that discovers "which route is this conductor running" today is `render.py`'s local `job_children.get(job.slug, [])` (keyed by the depth-2 child's `parent_slug`, populated in `dispatch.py:1026/1084/1165`) or, for a session-owner, `children.get(s.session_id, [])` (keyed by the child's `parent_sid`, populated in `dispatch.py:1025/1083/1166`) inside `_conductor_stage_override`/`_conductor_route_seq` (`render.py:2875-2910`) — i.e. the owner→children linkage lives entirely in render-time local dicts, not in any collector/projection module.

**Plan's assumption:** Step 1.3.5 says "For an owner/conductor, gather current child projections. Children from one validated route may contribute all parallel `active_nodes` without ambiguity," and Step 3.2.1 mandates deleting `_conductor_stage_override`/`_conductor_route_seq` so that "Group and process views must use `entity.work_projection` ... only." This requires the owner's *own* `work_projection.active_nodes` to already be correctly populated before Phase 3 renders it, but neither Step 1.3.2's per-entity evidence-priority order nor Phase 2's association step (scoped to *title/NOW/context* adoption via `(pid,proc_start)`/cwd — a different join) names `parent_slug`/`parent_sid`/`session_id` as the key the resolver uses to find an owner's children and inherit a `route_id` from them. Read literally, an owner with no direct route evidence resolves to `source=none` under 1.3.2 — contradicting F-36a's "owner/conductor represents 0+ parallel `active_nodes[]`" and making the Step 5.2 composed-DAG test (owner card showing `survey -> {claim-a,claim-b} -> synth` siblings) unsatisfiable without a Phase-1 rework discovered mid-Phase-3.

**Proposed correction:** Add one explicit rule to Phase 1 Step 1.3: *"An owner entity with no direct route evidence of its own resolves its route by locating child entities linked via `session_id`/`parent_sid` (Session owner) or `slug`/`parent_slug` (DispatchJob owner); if all such children carrying `route-exact` evidence agree on `route_id`, the owner adopts that `route_id` and reuses `route.py`'s existing route_id-keyed `build_views` grouping (already preserved per Step 1.2) for `active_nodes`; disagreement among children is ambiguous."* Without this one rule, Phase 1's resolver API risks not supporting what Phase 3 needs, forcing exactly the "dual stage authority" rework the plan's own Risk #1 warns against.

### plan step 1.3 / plan step 3.2 — `stage_label` has no deterministic route-exact definition

**Current code state:** `route._record_view()` exposes opaque node `id`, `assigned_contract`-adjacent metadata, and state (`tools/fleet/route.py:500-540`); the renderer currently chooses `route_node`/legacy role labels in `_dispatch_stage_label()` (`tools/fleet/render.py:1195-1213`) and may flatten a route into `route_seq` (`tools/fleet/render.py:736-785`).

**Plan's assumption:** The resolver copies exact `assigned_contract`/`unit`/state and says not to infer a stage from the node label (plan step 1.3.4), while rendering a leaf's opaque `stage_label` (step 3.2.2). It never says whether route-exact `stage_label` is the exact `route_node`, `assigned_contract`, a combined display label, or absent.

**Proposed correction:** Define the field-level mapping before implementation: for a validated route, `stage_label` must be a display-only exact value (prefer the explicit assigned contract when the contract is the approved human label, otherwise the opaque `route_node`; never semantic-map `plan/exec/test` names); registry-exact may expose only observed route/node labels; artifact-inferred may expose only the artifact stage. Add parity assertions for `research`/`claim-a` labels across group, process, plain, and JSON. Without this, the same projection can be “authoritative” yet render no stage or silently revive the fixed pipeline.

### plan step 2.2 / plan step 1.3.7 — artifact-root and QA lookup ownership is incomplete

**Current code state:** `_find_plan_dir()` deliberately prefers registry `artifact_root` for source-only worktrees (`tools/fleet/collectors/dispatch.py:675-692`), and `_plan_qa()` independently calls that helper (`:747-789`). `live_stage()` is invoked from process collection and registry reconciliation (`:1041-1042`, `:1440-1441`, `:1453-1456`). Existing tests pin source-only artifact-root behavior in `tools/fleet/tests/test_f15_rows.py:133-155`.

**Plan's assumption:** The strict exact artifact adapter moves behind `projection.py`, fuzzy selection disappears, `DispatchJob.stage` is copied from the projection, and QA collection remains intact. The plan does not carry `artifact_root` into the resolver contract or say how `_plan_qa()` retains its separate QA-only artifact read after `_find_plan_dir()` moves.

**Proposed correction:** Add `artifact_root` explicitly to the projection input/candidate search and require exact-cardinality enumeration across both the registry artifact root and the cwd-local reports root. Specify a separate named QA-artifact resolver (or an explicit projection API) so QA fallback does not call the stage adapter or accidentally inherit stage-only ambiguity semantics. Add a test for a unique source-only artifact-root candidate and a regression check that every stage call site is removed from dispatch/render while QA still resolves according to its declared precedence.

### plan step 2.5 / plan step 4.3 — OpenCode refresh source is not wired end-to-end

**Current code state:** OpenCode enrichment reads SQLite read-only and computes context/title (`tools/fleet/collectors/opencode.py:136-205`) but does not provide `_transcript_path` or a refresh cursor. `refresh_title.maybe_spawn()` rejects every harness except Claude/Codex and requires a transcript file (`tools/fleet/refresh_title.py:507-516`); its worker CLI only accepts those two harnesses and `--transcript` (`:619-645`); `read_delta()` is byte-offset/file based (`:186-205`).

**Plan's assumption:** It says to accept `opencode`, add a read-only exact-session message adapter, and advance an integer cursor, but does not define the source object or the changes connecting collector → scheduler → Popen argv → worker CLI → sidecar offset → SQLite query. “Only if cursor shape requires it” also leaves the required sidecar contract undecided.

**Proposed correction:** Specify an explicit ephemeral refresh-source contract, e.g. `{harness, session_id, db_path, cursor_kind, cursor}`; make `schedule_sessions()`/`maybe_spawn()` accept either a transcript source or this DB source; make the worker CLI mutually exclusive over `--transcript` and `--opencode-db/--opencode-session`; persist the integer cursor in the existing harness-namespaced sidecar; and define stable row ordering, exact `session_id` filtering, tool/internal/malformed-row exclusion, and DB `mode=ro`. Add a temp-DB test proving first/delta reads, cursor advance, malformed rows, and zero DB writes.

### plan step 3.3 / plan step 5.3 — Process-view detail-row integration and identity lookup are not specified

**Current code state:** `_build_lines()` resolves route views independently (`tools/fleet/render.py:2417-2429`), while process view builds route cards via `_route_card()` (`:2094-2175`). Process cards render active jobs with `_route_job_row()` and then sub-agent strips, but no context/NOW detail row; the process helper indexes sessions by PID only (`_build_process_lines`, `:2270`) and does not have child-context data.

**Plan's assumption:** Step 3.3 says the detail helper emits in group, process, and plain views, but all concrete instructions describe identity cards and group dispatch rows. Step 5.3 asserts four widths and ordering without identifying the process-card owner/child insertion point or replacing the PID-only lookup.

**Proposed correction:** Define the process-view unit of ownership: either add one detail row beneath each active node job and before its sub-agent strip using the job's associated child context, or explicitly state that only group identity cards receive it and remove “process view” from the plan. In the former case, pass attached projections into `_route_card()`, replace `session_by_pid` with exact `(pid,proc_start)` association, and add process-view assertions for context+NOW/context-only/NOW-only/unknown plus stale/dead suppression at the required widths.

## 🟡 Useful improvements

### plan step 1.1 / plan step 2.3 — make context sequence/freshness data a concrete contract

The plan correctly requires compaction decreases to remain valid and source-sequence regression to become `unknown`, but `ContextProjection` only mandates `used_pct`, `band`, and `source`; it does not define the sequence/freshness/reason fields or whether they are private. Current collectors only expose `ctx_pct` plus harness-specific counters. Add explicit ephemeral fields (or a documented adapter evidence object), define the public child JSON shape as `{used_pct, band, source}`, and name per-harness sequence sources in the tests.

### plan step 5.2 / plan step 5.5 — enumerate all superseded route/artifact tests

The plan names `test_f28_route.py`, `test_f28_breadcrumb.py`, and `test_f30_process_view.py`, but `test_f30_gate_passed.py:298` still asserts `source="heuristic"`, and `test_f15_rows.py` pins the old artifact lookup. Add these files explicitly to the affected-test list, alongside any `test_dispatch.py` assertions that inspect `live_stage()` or registry-only stage derivation. This prevents the full-suite gate from becoming the first discovery of a planned contract migration.

## 🟢 Well-constructed portions

- The dependency order and canonical-only ownership are clear: model/route/projection → collectors/association → surfaces → scheduler → tests → mirror.
- The plan faithfully carries the final independent specification PASS (`verdict-final-4.json`) and keeps implementation pending rather than treating the 179 baseline checks as v16 evidence.
- Evidence precedence, exact-cardinality artifact behavior, ambiguity codes, parallel-sibling preservation, context orthogonality, title quota/debounce, additive JSON, no-provider guards, compose/compiler verification, once/JSON smoke, mirror parity, and adaptation gates are all named with executable commands.
- The unrelated worktree `spec/prd.md`/pipeline state is correctly identified by the canonical component state as Unified Memory System rather than Fleet; the Fleet component pipeline state separately records v16 spec done and development pending.
- Independently re-verified: every "current state" citation in the plan resolves to real code at the cited lines (spot-checked `model.py:125-274`, `route.py:109-209/407-497/500-540/643-666`, `procscan.py:311-332`, `collectors/__init__.py:63-94`, `dispatch.py:675-744/1041/1440/1455`, `render.py:919-1004/1368-1459/1911-1921/2402-2445/2848-2958/2875-2910`, `fleet.py` in full, `refresh_title.py:45-51/208-231/507-625`), and every named existing test/fixture/script (`test_f28_route.py`, `test_f28_breadcrumb.py`, `test_mirror_parity.py`, `preflight.sh`, `compose_route.test.py`, `capability_route.test.py`, `adaptation-guard.test.sh`, `check-adaptation-boundary.sh`) exists and matches the described behavior, including the exact rsync mirror command (matches `test_mirror_parity.py`'s own documented command verbatim) and the `survey -> {claim-a,claim-b} -> synth` fixture naming (traced to the PRD's own acceptance-matrix row, not invented).

## Review evidence and checks

- Read the assigned plan and checklist completely, twice, in two independent passes.
- Read canonical Fleet v16 PRD §4.12 and the v16 module/diagram/Next sections, the research handoff, `verdict-final-4.json`, `owner-finalization.json`, and the Fleet component pipeline summary/state.
- Inspected the current model, route, collectors, renderer, fleet entrypoint, OpenCode/Claude/Codex enrichers, refresh scheduler, token budget, `compose-route.py`/`compose_route.test.py`, and affected tests read-only.
- Confirmed the task worktree's own `.agent_reports/spec/agent-fleet-dashboard/prd.md` is a stale shadow copy (547 lines, header capped at v15, no F-36~F-39/§4.12) — the canonical artifact root's copy (597 lines, v16, PASS-verdict) is the one the plan correctly cites and grounds against.
- `preflight.sh qa-policy standard code` passed with assurance `plan-check:selected-independent-pass:final-verify`.
- Unsupported detail retained from the approved evidence: the primary `.spec-grounding` marker side effect is read-only/unavailable; no live provider was invoked during this review.

