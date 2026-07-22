---
status: active
created: 2026-07-22
---

# Fleet v16 unified stage/context UI implementation plan

## Goal

Implement the approved agent-fleet-dashboard PRD v16 F-36 through F-39 so interactive sessions and registered dispatch jobs consume one fail-closed `WorkProjection`, sealed composed routes render as arbitrary fork/fan-in DAGs, every live identity card has exactly one context-first subordinate row, and the shared title/NOW scheduler obeys the approved 3/4 concurrency and 4-starts-per-60-seconds contract without invoking a live provider during verification.

## Approved scope and invariants

- Scope is implementation of F-36, F-37, F-38, F-39 and every row of the PRD §4.12 acceptance matrix. Earlier v2/v6/v8/v9/v10 implementation sequences are historical and must not be reopened.
- Fleet remains a read-only observer of harness state. The only writes remain Fleet-owned title sidecars/leases and the already-approved user-initiated control log path; this change must not write harness transcripts or state databases.
- Existing public JSON keys and meanings (`sessions`, `jobs`, `summary`, `route`) remain compatible. `work_projection`, child `context`, and machine-readable ambiguity data are additive.
- Exact explicit route evidence is authoritative. Any explicit but unverifiable route tuple fails closed; it is never covered by artifact inference or `_PIPE_STAGES`.
- Artifact inference is legal only when the entity has no route evidence at all and exactly one exact plan-directory candidate. It can provide only `stage_label`.
- A validated route record is opaque data. Node IDs and `depends_on` determine order; names such as `plan`, `exec`, `test`, or `report` have no special meaning on the validated-record path.
- Title, NOW, and context for a dispatched child come from one association result. A partial mix of sources and parent-context inheritance are forbidden.
- Context band changes can alter only context/NOW presentation. They cannot alter route topology/state, intensity, dispatch depth, model role/effort, QA/reviewer budget, tests, retries, completion gates, guards, or definition of done.
- All implementation tests are hermetic. Snapshot, demo, width, projection, scheduler, and storm tests must not call a default or custom live provider or signal a live process.
- Canonical Fleet files under `tools/fleet/` are the implementation source. `adapters/claude/tools/fleet/` is a byte-identical concrete mirror and is synchronized only after canonical behavior passes.

## Current state analysis

### Repository and approved evidence

- The worktree was clean when inspected at `340359eb5a12e175dc2b1f28212763df5f96b791`. There are no Fleet/compose/compiler changes between compose-on-demand commit `e8938809d87e54474f5e7242a2552598c2636a0a` and the inspected HEAD, so the current Fleet source is the same implementation baseline analyzed by the approved research handoff.
- The canonical PRD is v16 and locks F-36 through F-39 plus the complete acceptance matrix at `spec/agent-fleet-dashboard/prd.md:356-400`.
- The approved research handoff identifies the current parity gaps and records 166 passing baseline checks. The final specification review is `PASS` and explicitly states that v16 development remains pending; it records 179 passing baseline checks without claiming implementation evidence.
- No Fleet-specific `analysis_project/code/` artifact exists. The present analysis files concern Skill design and installer work, so none is a relevant module/data-flow input for this Fleet plan. The approved Fleet research shard is therefore the relevant prior analysis.
- The owner-side `preflight.sh read <prd> codex-headless` marker side effect is degraded: the hook reports a read-only `.spec-grounding` location even though the PRD read itself succeeds. This unsupported guard detail must remain visible in the code-cycle report; it must not be claimed as a successful spec-read marker.

### Model and collection gaps

- `tools/fleet/model.py:125-181` defines `Session` with context/title/summary but without route identity or a shared work projection. `tools/fleet/model.py:203-274` defines `DispatchJob` with route/attempt/contract/unit data and child title/summary, but without child context or a common projection. Both `to_dict()` methods currently use `dataclasses.asdict`, so nested additive dataclasses can be serialized without replacing old fields.
- `tools/fleet/collectors/procscan.py:311-332` reads each process environment once and uses dispatch markers only for child attribution. It currently discards `AGENT_ROUTE_FILE`, `AGENT_ROUTE_ID`, `AGENT_ROUTE_NODE`, `AGENT_DISPATCH_ASSIGNED_CONTRACT`, and `AGENT_DISPATCH_UNIT` when constructing a `Session`, even though this is stronger evidence than cwd/artifact inference.
- `tools/fleet/collectors/__init__.py:63-94` adopts only title and summary. It indexes strong matches by PID alone rather than `(pid, proc_start)`, builds its cwd index only from children that already have title/summary, and does not record an ambiguity reason. This permits PID reuse to misassociate data and prevents context from sharing the same decision.
- `tools/fleet/collectors/dispatch.py:675-744` locates plan directories with an exact-suffix attempt followed by fuzzy token-overlap/latest-mtime selection. `live_stage()` then synthesizes `plan/exec/test/done`. It is called during process collection (`tools/fleet/collectors/dispatch.py:1040-1044`) and again for registry-only rows near the end of collection, so stage is currently decided before a route-aware common resolver can enforce evidence precedence.
- Claude, Codex, and OpenCode collectors already calculate `ctx_pct`, but they do not expose a common context source/sequence contract. `tools/fleet/collectors/opencode.py:64-107,136-205` can read per-message tokens and session metadata from SQLite in read-only mode, but it neither applies Fleet sidecar title/NOW precedence nor exposes an OpenCode conversation source to the title refresher.

### Route and composed-DAG gaps

- `tools/fleet/route.py:109-209` validates schema v1/v2 records and sealed hashes, but `load()` returns only `record|None`; callers cannot distinguish an absent route from an explicit mismatch in a stable machine-readable way.
- `tools/fleet/route.py:407-432` already performs record-order Kahn leveling and preserves fork/fan-in topology. `tools/fleet/route.py:500-540` preserves node ID, dependencies, unit, unit choices, gate, state, and progress, but omits `write_scope` from the view. `tools/fleet/route.py:643-665` similarly omits `write_scope` from public route JSON.
- `tools/fleet/route.py:489-497,543-581` produces a `source="heuristic"` empty view when a named record cannot be loaded. That is no longer sufficient: an explicit invalid tuple needs `unknown` plus a stable ambiguity code and must not invite fixed-pipeline fallback.
- `utilities/compose-route.py:103-170` at commit `e8938809` already fails closed when a completion gate is absent or ambiguous and preserves arbitrary `id`, `unit`, `depends_on`, `completion_gate`, and `write_scope` before invoking the canonical compiler. `utilities/compose_route.test.py:107-147` already pins the sealed compile/verify round trip and ambiguous-gate refusal. These utilities are dependencies to verify, not logic to duplicate in Fleet.
- Existing Fleet route tests already pin a lab fork/fan-in (`tools/fleet/tests/test_f28_route.py:116-133`) and non-code labels such as `eval-sep` and `research` (`tools/fleet/tests/test_f28_breadcrumb.py:81-117`). The new implementation should extend these fixtures rather than replace them.

### Rendering and JSON gaps

- The wide session row still renders an inline expanding context gauge (`tools/fleet/render.py:919-1004`). Narrow cards render context on L2 and stack cards split the same gauge onto L3 (`tools/fleet/render.py:1368-1459`). Those paths conflict with F-37's one subordinate-line contract.
- The existing NOW helper is `_summary_row()` (`tools/fleet/render.py:1911-1921`). Group assembly emits it only in the wide branch for dispatch jobs and sessions (`tools/fleet/render.py:2848-2854,2953-2958`), so narrow/stack omit NOW.
- `tools/fleet/render.py:2402-2445` resolves route views inside the renderer, and the conductor helpers select the first active routed child and first available route ID (`tools/fleet/render.py:2875-2910`). This both duplicates stage authority and loses valid parallel siblings/conflicting-route ambiguity.
- `tools/fleet/fleet.py:82-102` serializes sessions/jobs and separately recomputes route summary. `tools/fleet/fleet.py:152-190` correctly schedules title workers only in the live TUI path; `--json` and `--once` do not schedule them. The new projection must be attached before every render/JSON surface without changing that no-spawn boundary.

### Title/NOW scheduler gaps

- `tools/fleet/refresh_title.py:45-51` currently sets concurrency `2`, hard max `4`, start budget `3`, hard max `3`, and a 60-second window. Debounces already match v16 at main `600s` and child `150s`.
- The provider interface is already shell-free and the default provider denies all tools (`tools/fleet/refresh_title.py:259-283`). Cross-process fail-closed guards, slot leases, rolling-start leases, stale reclamation, kill switches, and direct-`run_worker()` enforcement already exist (`tools/fleet/refresh_title.py:293-500`). These mechanisms should be retained while changing only the approved numeric limits and coverage.
- `maybe_spawn()` and the worker CLI accept only Claude/Codex (`tools/fleet/refresh_title.py:507-516,619-625`). `schedule_sessions()` otherwise treats ordinary child sessions correctly and excludes mem/title workers, app-server, dead, and stale rows (`tools/fleet/refresh_title.py:592-616`). OpenCode must be added through a read-only message adapter rather than excluded by harness name.
- `validate_title()` enforces the 40-character and maximum-six-word bounds but does not enforce the approved minimum of three words (`tools/fleet/refresh_title.py:208-231`).

## Implementation ownership and dependency order

Canonical ownership is exclusive by phase; do not edit the Claude mirror in parallel with canonical files.

| Owner/phase | Files owned | Responsibility | Dependency |
|---|---|---|---|
| Phase 1 — projection/model | `tools/fleet/projection.py` (new), `tools/fleet/model.py`, `tools/fleet/route.py`, `tools/fleet/token_budget.py` only if a reusable pure context helper is required | Define additive public projections plus private context evidence, exact leaf and owner/conductor route resolution, deterministic stage-label provenance, artifact-root/cardinality rules, ambiguity codes, and arbitrary-DAG metadata | None |
| Phase 2 — evidence/association | `tools/fleet/collectors/__init__.py`, `tools/fleet/collectors/procscan.py`, `tools/fleet/collectors/dispatch.py`, `tools/fleet/collectors/claude.py`, `tools/fleet/collectors/codex.py`, `tools/fleet/collectors/opencode.py` | Capture source evidence, replace the title-only join with one child association, normalize each session's context, attach projection once per snapshot, preserve a separate QA-only artifact lookup, and expose an OpenCode read-only refresh source | Phase 1 contracts |
| Phase 3 — surfaces | `tools/fleet/render.py`, `tools/fleet/fleet.py`, `tools/fleet/demo.py` | Consume attached projections only, render arbitrary DAG/fan-in, add the single detail row in all layouts/views, preserve additive JSON and no-spawn snapshot behavior | Phases 1-2 |
| Phase 4 — scheduler | `tools/fleet/refresh_title.py`, `tools/fleet/titles.py` | Apply 3/4 and 4/60 limits, enforce the 3-6-word title validator, carry transcript/SQLite refresh sources through scheduler and CLI, persist a typed integer OpenCode cursor in the existing sidecar, and retain shared leases/kill switches/no-tools boundary | Phase 2 OpenCode source contract; otherwise parallel with Phase 3 |
| Phase 5 — tests/fixtures | `tools/fleet/tests/test_f36_work_projection.py` (new), `test_f37_context_detail.py` (new), `test_f38_context_orthogonality.py` (new), `test_f39_title_quota.py` (new), `tools/fleet/tests/fixtures/route/synth_composed_survey.json` (new), and the affected existing Fleet tests named below | Pin every acceptance row and regression boundary, including no-live-provider enforcement and old-key JSON consumer | Phases 1-4 |
| Phase 6 — mirror/final verification | `adapters/claude/tools/fleet/**` mirror only | Synchronize the fully passing canonical Fleet tree byte-for-byte, then run mirror/adaptation gates | Phase 5 pass |

## Change plan

### Phase 1: Introduce the common projection and fail-closed route authority

#### Step 1.1 — Add additive model contracts

Target: `tools/fleet/model.py`.

1. Add a public `ContextProjection` dataclass whose serialized shape is exactly `used_pct`, `band`, and `source`. Add a private/non-serialized `ContextEvidence` value (dataclass or equivalent) with `used_pct`, `source`, comparable `sequence`, `source_head_sequence`, `observed_at`, `fresh_until`, and an internal invalidity reason. Keep the legacy `ctx_pct` field.
2. Add a `WorkProjection` dataclass with the exact approved fields: `source`, `route_id`, `route_hash`, `route_node`, `attempt_id`, `assigned_contract`, `unit`, `stage_label`, `node_state`, `active_nodes`, nullable `progress`, and `ambiguity`.
3. Add optional route/env evidence and `work_projection`/normalized `context` fields to `Session`. Add `work_projection`, child `context`, and association ambiguity fields to `DispatchJob`. Defaults must make old constructors/tests valid.
4. Preserve every old field and its type. Ensure `Session.to_dict()` and `DispatchJob.to_dict()` serialize the new public nested values additively while excluding `ContextEvidence`, refresh-source paths, and ephemeral/private route-view caches.
5. Keep context and work projection separate in the data model so a context band update cannot mutate orchestration fields by construction.

#### Step 1.2 — Make route validation diagnostic and preserve all opaque node metadata

Target: `tools/fleet/route.py`.

1. Add a diagnostic load helper that distinguishes validated records from explicit failure without weakening existing `load()` callers. Normalize explicit failures to `route-record-mismatch`; do not expose parser internals as unstable ambiguity strings.
2. Extend validated node views and `route.summary()` to carry `write_scope` in addition to `id`, `depends_on`, `unit`, `unit_choices`, `gate`, and state. Preserve record order within each topological level.
3. Replace the explicit-invalid `heuristic` interpretation with an unresolved/unknown view carrying stable ambiguity. A route ID with a missing, corrupt, hash-mismatched, identity-mismatched, or future-schema record must have no fabricated nodes, progress, gate passage, or `_PIPE_STAGES` route.
4. Keep schema-v1 compatibility read-only and schema-v2/dispatch-contract-v3 hash checks unchanged. Fleet must not recompile unit catalogs or derive a gate from unit names.
5. Retain `node_order()` as the only DAG ordering primitive and use `depends_on` only. Ensure duplicate/invalid evidence never changes the sealed record's topology.

#### Step 1.3 — Implement the source-agnostic resolver

Target: new `tools/fleet/projection.py`.

Implement pure or explicitly clock-injected helpers plus one snapshot attachment entry point:

1. Build entity candidate indexes for exact `(pid, proc_start)`, `Session.session_id -> DispatchJob.parent_sid`, `DispatchJob.slug -> DispatchJob.parent_slug`, and fallback `(harness, realpath(cwd))`. Never key a strong match by PID alone, and keep the owner-child route join distinct from the child title/NOW/context association.
2. Resolve one leaf with this precedence:
   - validated sealed record plus matching explicit entity route/node/attempt evidence → `route-exact`;
   - exact jobs.log/env identity without a validated record → `registry-exact`, preserving only observed identity fields and setting topology/progress/gate/completion to no-claim;
   - no exact identity and exactly one same-harness realpath-cwd registered candidate → the same registry outcome;
   - no route evidence anywhere and exactly one exact artifact plan directory → `artifact-inferred` with `stage_label` only;
   - otherwise `none`, with stable ambiguity codes as applicable.
3. Treat any nonempty explicit route tuple as a bar to artifact fallback. Partial/mismatched tuples get `route-record-mismatch`. Two route/node candidates for one leaf get `multiple-leaf-candidates`; two cwd candidates get `multiple-child-cwd-candidates`; two exact plan directories get `multiple-artifact-plan-dirs`.
4. For route-exact leaves, verify that `route_node` exists in the sealed record and copy its exact `assigned_contract`/`unit`/state. Define `stage_label` deterministically as the exact nonempty `assigned_contract` only when that value comes from the selected exact jobs.log/env evidence for the same validated `route_id`/`route_node` and, when present, `attempt_id`; otherwise use the sealed opaque `route_node`. Never derive it from `unit`, worker role, capability, key, or fixed `plan/exec/test/report` semantics. A registry-exact projection may expose only its observed contract/node label, and an artifact-inferred projection may expose only its exact artifact stage.
5. Resolve an owner/conductor that has no direct route tuple by traversing explicit parent links, not cwd or render-local ordering: for a `Session` owner select child jobs with `child.parent_sid == owner.session_id`; for a depth-1 `DispatchJob` owner select child jobs with `child.parent_slug == owner.slug`. Consider only current `route-exact` child projections. If they all agree on one validated `route_id` and sealed hash, attach that route to the owner and reuse `route.py`'s route-id-keyed `build_views` result to populate every record-ordered parallel `active_node`; zero qualifying children leaves `source=none`. More than one route/hash, or a direct owner route that conflicts with a child route, fails closed with stable `multiple-owner-routes` or `owner-route-conflict` ambiguity rather than choosing the newest, first, or one child node. Different nodes on the same validated route are valid siblings, not ambiguity.
6. Preserve validated route levels and node metadata as ephemeral projection backing data so group/process/plain/JSON consumers can format the same result without reopening route files or calling `live_stage()`.
7. Make `artifact_root` an explicit resolver input. Enumerate the realpath-deduplicated union of exact `_<slug>` plan-directory matches beneath the registry `artifact_root` and the cwd-resolved local reports root; do not prefer mtime, token overlap, or `cand[-1]`. Exactly one distinct candidate is accepted, zero is `none`, and more than one is `multiple-artifact-plan-dirs`. Artifact inference must never populate route ID/node, progress, gate, or completion.
8. Normalize context with `token_budget.policy_band()` thresholds (`tight>=70`, `critical>=85`) and an injected clock. Reject malformed evidence, `observed_at > fresh_until`, or `sequence < source_head_sequence` as `unknown`; accept a lower percentage when its sequence is the current/newer source head because that is valid compaction. The private reason explains unknown during tests, while public child JSON remains exactly `{used_pct, band, source}`.

Completion dependency: Phase 2 may start only after the dataclasses, ambiguity vocabulary, and resolver API are stable.

### Phase 2: Capture exact evidence and unify child title/NOW/context association

#### Step 2.1 — Capture session route evidence at process-scan time

Target: `tools/fleet/collectors/procscan.py`.

1. Reuse the already-read process environment to populate optional Session route fields: `AGENT_ROUTE_FILE`, `AGENT_ROUTE_ID`, `AGENT_ROUTE_NODE`, assigned contract, unit, worker type, owner, and model role where present.
2. Preserve `(pid, proc_start)` as the strong identity. Do not infer an attempt ID that the runtime does not export; let exact jobs.log association supply it when available.
3. Keep `AGENT_SESSION_ROLE=worker` as attribution evidence only. It must not itself exclude an ordinary conversational child from title/NOW scheduling.
4. Preserve all existing app-server, mem-worker, detached, and process-discovery behavior.

#### Step 2.2 — Remove independent stage judgment and separate QA artifact lookup

Target: `tools/fleet/collectors/dispatch.py`.

1. Continue collecting raw jobs.log/env fields, attempts, route tuple, `artifact_root`, liveness, and legacy `stage` inputs, but stop calling `live_stage()` as an independent authority during process scan or registry reconciliation.
2. Move the strict exact stage-artifact adapter behind `projection.py`. Its candidate enumerator accepts both `job.artifact_root` and cwd, searches both declared roots, realpath-deduplicates exact suffix matches, and exposes cardinality; any compatibility `live_stage()` wrapper must be projection-private and incapable of fuzzy selection or route/progress/gate synthesis.
3. Add a separately named QA-only resolver such as `resolve_plan_qa_artifact(job)`. It runs only after explicit argv/jobs.log QA is absent, may reuse the pure exact plan-directory enumerator, requires exactly one distinct candidate, and returns only the plan's QA value or `None`; it never calls the stage adapter, emits a stage label/route ambiguity, or inherits stage fallback semantics. Thread `artifact_root` into this QA fallback so source-only worktrees retain their current support.
4. After projection, populate the existing `DispatchJob.stage` compatibility field from `work_projection.stage_label` so old consumers retain a stage string without creating a second source of truth.
5. Preserve terminal node evidence and current-attempt filtering. Ensure a record-less explicit tuple remains `registry-exact`/unknown and cannot become a fixed `plan/exec/test/report` breadcrumb.
6. Keep existing job liveness semantics intact; context projection must not alter QA or liveness.

#### Step 2.3 — Normalize context evidence per harness

Targets: `tools/fleet/collectors/claude.py`, `tools/fleet/collectors/codex.py`, `tools/fleet/collectors/opencode.py`.

1. For each collector, retain the legacy `ctx_pct` and token counters while producing the private `ContextEvidence` contract from Step 1.1. Evidence ordering is comparable only within the same harness/source and carries both the selected sample sequence and the source head sequence.
2. Claude: use the exact session's statusline/transcript observation only; sequence it with the transcript observation order `(mtime_ns, byte/event offset)` and derive freshness from the existing exact-session liveness/currentness window. Never borrow a same-cwd neighbor's context.
3. Codex: use the exact rollout token-count observation already owned by the session; sequence it with rollout file order `(mtime_ns, JSONL byte/event offset)` so an older event or file cannot replace a newer one.
4. OpenCode: use the matched session's read-only message/session observation and model denominator; sequence it with stable DB order `(time_updated, rowid)` from the selected compatible table. Keep per-message prompt tokens preferred over cumulative session tokens.
5. Set malformed/missing/stale values, cross-source sequence comparisons, and selected-sequence-before-head cases to unknown rather than clamping or copying another session. Allow a lower value from a newer valid sample. Serialize only the normalized `{used_pct, band, source}` projection.

#### Step 2.4 — Replace `_adopt_child_titles` with one ambiguity-refusing association

Target: `tools/fleet/collectors/__init__.py`.

1. Build candidate sets from all enriched child sessions, not only children that already have a title or summary.
2. Strong match: require exact `(pid, proc_start)` on both job and child. If a PID is reused, proc-start differs, or the exact key has multiple candidates, refuse the association and do not fall through to cwd.
3. Fallback only when exact identity is unavailable: require exactly one `(harness, realpath(cwd))` child. Reject two candidates and all cross-harness candidates.
4. From the one selected child, copy title, fresh NOW/summary, and normalized context together. If association fails, withhold all three and record machine-readable ambiguity. Never retain a title from one child while taking NOW/context from another.
5. Never copy context from the parent session. A live job with no valid child context renders `ctx —`.
6. Order snapshot assembly as: process/enrichment → liveness/jobs → child marking → session context normalization → one child association → work projection attachment. Attach a `WorkProjection` to every Session and DispatchJob, including `source=none`.

#### Step 2.5 — Add OpenCode sidecar/source parity without writing its DB

Target: `tools/fleet/collectors/opencode.py`.

1. After exact session selection, apply fresh Fleet sidecar title/NOW precedence before the native OpenCode title; preserve native title as fallback.
2. Attach a private, non-serialized refresh-source value with the explicit shape `{kind: "opencode-db", harness: "opencode", db_path, session_id, table, cursor_kind: "opencode-rowid-v1:<table>", observed_cursor}`. Choose the first compatible message table from a fixed documented precedence, require an integer SQLite `rowid`, and compute `observed_cursor` for that exact session only. Claude/Codex expose the parallel `{kind: "transcript", harness, session_id, path, cursor_kind: "byte-offset-v1"}` shape so the scheduler has one typed input contract.
3. Do not serialize either source path or write the live SQLite/WAL/SHM files. The refresher may use a consistency-checked ephemeral private snapshot of the database plus an existing WAL; persistent copies remain forbidden. All OpenCode queries use private-snapshot URI `mode=ro&cache=private`, exact `session_id`, parameter binding, and stable `ORDER BY rowid ASC`.
4. Treat ordinary registered conversational OpenCode children like Claude/Codex children; exclude only the cross-harness internal predicates already locked by F-39.

### Phase 3: Make all display and JSON surfaces consume the projection

#### Step 3.1 — Project once before surface selection

Target: `tools/fleet/fleet.py`.

1. Ensure live, `--once`, `--json`, demo, group, and process paths receive sessions/jobs with attached projections from one snapshot pass.
2. Change `_collect_route()` to serialize the validated route views backing the attached projections instead of rerunning route resolution. Existing top-level `route` remains present and keeps its old fields, with `write_scope`/ambiguity additive.
3. Keep `--json` and `--once` outside the scheduler wrapper. Projection and rendering must never start a provider.
4. Add a small old-key-only JSON consumer test that reads only the pre-v16 keys and succeeds unchanged.

#### Step 3.2 — Replace all stage first-match logic with projection formatting

Target: `tools/fleet/render.py`.

1. Delete the renderer's route-file resolution and `active_routed[0]`/first-route-ID decisions. Group and process views must use `entity.work_projection` and its validated route-level backing data only.
2. For a leaf, display the already-resolved `stage_label`: exact selected `assigned_contract` when it is the validated human label for that leaf, otherwise exact opaque `route_node`. For an owner with one child-agreed validated route, display every active sibling in record order. A compact group breadcrumb may format one topological level as a branch set (for example `{claim-a● | claim-b●}`), but it must not flatten away parallelism, relabel `research`/`claim-a`, or invent a fixed pipeline.
3. Preserve process-view vertical fork/fan-in rendering using route levels, and include `unit`, gate, scope, state, and progress from the same projection. Do not expose `_PIPE_STAGES` for any explicit tuple, valid or invalid.
4. Permit the historic fixed breadcrumb only for a genuinely route-absent `artifact-inferred`/legacy projection. Explicit-invalid projections show unknown/ambiguity.
5. Ensure plain `--once` uses the same `_build_lines()` result as live TUI and process/group views; no separate stage judgment is allowed.

#### Step 3.3 — Implement exactly one context-first subordinate row in every layout

Target: `tools/fleet/render.py`.

1. Remove context from `_session_row()`'s wide primary row, `_session_row_2line()` telemetry, and `_session_row_stack()`'s gauge line. Retire `_wide_ctx_width()` as a layout contract; preserve branch/model/time alignment and use freed primary-row width for the stage/progress zone.
2. Replace `_summary_row()` with a context-detail helper that accepts the owner projection/context, fresh NOW, depth, liveness, and terminal width. Render exactly:
   - context+NOW: `ctx 63% normal · <NOW>`;
   - context only: `ctx 63% normal`;
   - NOW only: `ctx — · <NOW>`;
   - neither: `ctx —`;
   - stale/dead: no detail row.
3. Emit the helper after the complete identity card (all wide/narrow/stack identity lines) and before its sub-agent strip in group view and plain output. Dispatch depth must use the same inset ladder as its sub-agent strip.
4. Reserve the full context token first. Clip only NOW with `_clip_w()` and display-cell width `_dw()` so ASCII/CJK text never splits a display cell and total row width is `<= term_width`.
5. Ensure wide@168, forced wide@120, narrow@100, and stack@60 each contain one and only one detail row. Do not emit a blank separator when NOW is absent.
6. Define process-view ownership explicitly. `_build_process_lines()` creates `session_by_identity[(pid, proc_start)]`, never `session_by_pid`; `_route_card()` and `_degrade_card()` receive this exact map plus attached job projections. Beneath each live active-node or degrade `DispatchJob` identity row, emit exactly one detail row from that job's atomically associated child `context`/fresh NOW, then its exact-session sub-agent strip. A missing/mismatched identity cannot supply a strip or substitute context; stale/dead jobs emit neither detail nor cached NOW. Route-card headers do not receive an extra detail row.
7. Preserve stale/dead honest degradation and existing title/branch/model/time columns. Parent and child rows use their own normalized context objects.

#### Step 3.4 — Update demo fixtures without provider side effects

Target: `tools/fleet/demo.py`.

1. Populate deterministic WorkProjection/context examples for route-exact, artifact-only, unknown, missing-context, and child-context rows.
2. Include a fork/fan-in composed route example suitable for group/process/plain smoke output.
3. Demo remains data injection only and never schedules a title provider; tests must fail immediately if `Popen` or provider `run` is reached.

### Phase 4: Raise the shared title/NOW quota and add OpenCode conversational input

#### Step 4.1 — Apply the approved single numeric contract

Target: `tools/fleet/refresh_title.py`.

1. Set default concurrency to `3`, hard maximum to `4`.
2. Set default and hard start limit to `4` with rolling window `60s`.
3. Keep main debounce `600s` and child debounce `150s`.
4. Keep one shared cross-process slot/start pool for main/child and default/custom providers. Direct `run_worker()` must continue to acquire both guards when capacity is not already held.
5. Preserve nonblocking fail-closed guard behavior, per-session lock, stale slot reclamation, `FLEET_TITLE_DISABLE`, state-file kill switch, and `0` disable semantics. Invalid environment values return to safe defaults and overrides clamp to the hard maximums.

#### Step 4.2 — Enforce the current TITLE and provider boundary

Target: `tools/fleet/refresh_title.py`.

1. Enforce 3-6 words and at most 40 characters in `validate_title()`; older 4-8/64 and 8-12/96 contracts must not remain active.
2. Keep NOW as a separately validated, conversation-language, one-line value with sidecar freshness controlled by `titles.py`.
3. Retain default Claude/Haiku tool denial and shell-free `shlex` argv substitution for `FLEET_TITLE_COMMAND`/`FLEET_TITLE_MODEL`. Do not claim Fleet can inspect a custom wrapper's no-tools property; that remains wrapper-owned.
4. Keep provider output untrusted data and preserve current independent title/NOW degradation.

#### Step 4.3 — Add a tolerant read-only OpenCode delta adapter

Targets: `tools/fleet/refresh_title.py` and `tools/fleet/titles.py`.

1. Change `schedule_sessions()` to pass the private typed refresh source from Step 2.5, and change `maybe_spawn()` to accept either a transcript source or an OpenCode DB source. Validate source kind, exact session ID, path existence, cursor kind, and observed-cursor growth before acquiring leases; never treat a DB path as a transcript.
2. Build worker argv from the source kind. Transcript jobs pass `--transcript`; OpenCode jobs pass both `--opencode-db` and `--opencode-session`. Extend `--harness` with `opencode`, use an argparse mutually exclusive source group, and reject a lone DB/session argument or a source inconsistent with the harness before provider execution.
3. Add `read_opencode_delta(db_path, session_id, last_cursor)` that opens `file:...?mode=ro`, chooses the same fixed compatible table contract as the collector, executes an exact-session parameterized `rowid > ? ORDER BY rowid ASC` query, and returns normalized conversation text plus the largest consumed integer rowid. Normalize only user/assistant text; skip tool/internal payloads, malformed JSON, wrong-session rows, and incompatible tables without advancing past unread valid data.
4. Extend the existing harness-namespaced sidecar additively with `cursor_kind`; continue storing the integer cursor in its compatible `offset` field. Use `byte-offset-v1` for Claude/Codex and `opencode-rowid-v1:<table>` for OpenCode. A missing/mismatched cursor kind starts that source at zero rather than reinterpreting a transcript byte offset or another table's rowid. Preserve old sidecar reads and fields.
5. Feed the worker's returned cursor through `titles.write()` on empty-delta, rejected-title, and successful-title paths so every consumed batch advances exactly once. Sidecar/title files remain the only persistent writes; a consistency-checked ephemeral private DB+WAL snapshot is allowed, while persistent copies and source DB/WAL/SHM writes remain forbidden.
6. Keep ordinary OpenCode conversational children eligible after 150 seconds. Keep mem/title workers, app-server, dead/stale rows, and source-less nonconversational loop/cron rows excluded. Claude, Codex, and OpenCode share the same slot/start pool and harness-namespaced sidecar rules.
7. Keep `--json`, `--once`, demo, snapshot, width, and test paths outside scheduling; hermetic tests patch both provider execution and worker spawn to fail if reached.

### Phase 5: Acceptance fixtures and regression tests

#### Step 5.1 — WorkProjection/evidence/cardinality suite

New target: `tools/fleet/tests/test_f36_work_projection.py`.

Cover:

- Equivalent exact evidence passed once as `Session` and once as `DispatchJob`; assert byte-equivalent normalized route/node/state/progress.
- Exact `route_node=research` beating an artifact folder implying `test`.
- Any explicit invalid/partial/mismatched tuple plus plausible artifact path yields `unknown`/`route-record-mismatch`, never artifact fallback.
- Artifact candidates: exactly one → `artifact-inferred` and stage only; zero → `none`; two → `none` plus `multiple-artifact-plan-dirs`. Assert route/node/progress/gate/completion are absent on all artifact paths.
- Two leaf route/node candidates and two cwd registered candidates fail closed. One same-route parallel active set is preserved in `active_nodes` without ambiguity.
- A Session owner discovers children only through `session_id == parent_sid`; a depth-1 DispatchJob owner discovers children only through `slug == parent_slug`. One shared sealed route populates all record-ordered active siblings; two route IDs/hashes and direct-owner/child conflict produce the named ambiguity and never choose the first child.
- Registry-only evidence preserves only observed identity and cannot fabricate topology, progress, gate, or node completion.
- A source-only worktree resolves one exact plan directory through registry `artifact_root`; two distinct directories across registry and cwd-local roots fail cardinality. QA fallback still reads a unique plan QA value through `resolve_plan_qa_artifact()` after argv/jobs.log precedence and never calls stage resolution.
- Renderer, process view, plain output, and JSON use the attached projection; monkeypatch legacy `live_stage()`/route load to fail if called after attachment.

#### Step 5.2 — Sealed composed DAG suite

Targets: new `tools/fleet/tests/fixtures/route/synth_composed_survey.json`, updates to `tools/fleet/tests/test_f28_route.py`, `test_f28_breadcrumb.py`, and `test_f30_process_view.py`.

1. Generate and check in a hash-sealed schema-v2/dispatch-contract-v3 route with `survey -> {claim-a, claim-b} -> synth`, opaque IDs, distinct units, gates, scopes, and two simultaneously active siblings.
2. Assert record-order topological levels, branch/fan-in, all active siblings, `write_scope`, unit/gate metadata, and correct progress in projection, group, process, plain, and top-level route JSON.
3. Retain and rerun the existing lab fork/fan-in fixture.
4. Assert `_PIPE_STAGES` text is absent for sealed and explicit-invalid records.
5. Keep compose compiler ambiguity refusal in `utilities/compose_route.test.py`; Fleet must consume the sealed result without re-deriving gates.
6. Assert route-exact label parity in group, process, plain, and JSON: a validated leaf with exact `assigned_contract=research` renders `research`; a `claim-a` node without a validated explicit contract renders the opaque `claim-a`. No surface semantically remaps either label.

#### Step 5.3 — Context association/layout/orthogonality suite

New targets: `tools/fleet/tests/test_f37_context_detail.py`, `tools/fleet/tests/test_f38_context_orthogonality.py`.

Update/replace affected assertions in `test_f16_f17_subtitle.py`, `test_dispatch_child_titles.py`, and `test_wide_ctx_gauge.py`.

1. Pin one row at wide@168, wide@120, narrow@100, stack@60 with order `identity card -> ctx … [· NOW] -> sub-agent strip`, CJK-safe clipping, and width bound in group/plain output.
2. Pin context+NOW, context only, NOW only, neither, stale, and dead separately. Live neither must render `ctx —`; stale/dead must render no detail row.
3. Exact `(pid, proc_start)` copies title/NOW/context as one bundle. Parent and child percentages differ to prove no inheritance.
4. Pin PID reuse, duplicate PID candidates, two same-cwd candidates, and cross-harness candidates; all three values are withheld together and ambiguity is exposed.
5. At 69/70/85 percent, compare a canonical serialization of every non-context field and require byte identity. Only context band/rendering may differ.
6. A newer sequence with a lower percentage is valid compaction. A lower source sequence, stale sample, malformed sample, or missing sample is unknown.
7. Pin process view separately: each live active-node and degrade job owns exactly one detail row immediately after `_route_job_row()` and before its sub-agent strip; route headers have none. Cover context+NOW, context-only, NOW-only, unknown, stale, and dead at 168/120/100/60 widths, and prove equal PID with unequal `proc_start` cannot supply context/NOW/sub-agents.
8. Pin the private evidence contract per harness: Claude `(mtime_ns, transcript event offset)`, Codex `(mtime_ns, rollout event offset)`, and OpenCode `(time_updated, rowid)`. Assert `sequence < source_head_sequence` and expired freshness become public unknown while the serialized child context has only `used_pct`, `band`, and `source`.

#### Step 5.4 — Scheduler/no-provider/JSON compatibility suite

New target: `tools/fleet/tests/test_f39_title_quota.py` plus updates to `test_f17_title_refresh.py` and `test_f21_cross_harness_titles.py`.

1. Fake clock + isolated state root + 200-session backlog: default live workers never exceed 3; override clamps at 4; slots may return but total starts in one rolling 60-second window never exceeds 4; fifth start fails; start resumes after the window.
2. Call `run_worker()` directly and prove it cannot bypass slot/start leases.
3. Verify stale worker leases are reclaimed and both kill switches produce zero starts.
4. Verify main `600s` and child `150s` debounce for Claude, Codex, and OpenCode ordinary conversational children. Internal/nonconversational exclusions remain zero-call.
5. Verify 3-6-word/40-character title validation, default disallowed-tools argv, and custom shell-free argv. Do not claim custom-wrapper tool denial beyond its contract.
6. Build a temporary OpenCode DB and assert the entire collector → private source → scheduler → argv → mutually exclusive CLI → `mode=ro` reader → typed sidecar cursor path. Prove first and delta reads, exact-session filtering, fixed-table/rowid order, cursor advance on empty/rejected/success paths, cursor-kind mismatch reset, malformed/tool/internal exclusion, and unchanged DB/WAL/SHM bytes/write metadata.
7. Patch both `subprocess.Popen` and provider `subprocess.run` to fail if reached, then exercise `fleet.main --json`, `fleet.main --once`, demo, all width fixtures, projection tests, composed-DAG tests, and the 200-session storm fixture. Expected live/default/custom provider calls: zero.
8. Feed `_snapshot_json()` to an old-key-only consumer and assert existing keys/field meanings. Assert new `work_projection` and child `context` are additive and null/unknown where evidence is absent; assert private refresh-source, DB path, `ContextEvidence`, and route backing objects are absent.

#### Step 5.5 — Preserve broader Fleet regressions

Run the entire canonical `tools/fleet/tests` discovery suite, not only new modules. Update old expectations only where F-36/F-37/F-39 explicitly supersede behavior:

- wide inline/expanding context gauge;
- narrow/stack inline context telemetry;
- wide-only summary row;
- first-active-child conductor selection;
- explicit-invalid route heuristic/fixed-pipeline fallback;
- title concurrency/start values and minimum word count.

The migration worklist explicitly includes `tools/fleet/tests/test_f30_gate_passed.py` (replace the explicit-invalid `source="heuristic"` expectation), `tools/fleet/tests/test_f15_rows.py` (replace `live_stage()` and artifact-root precedence assertions with projection/cardinality plus separate QA assertions), and `tools/fleet/tests/test_dispatch.py` (replace conductor first-child/fixed-stage and registry-stage derivation assertions). Search the full test tree for `live_stage`, `_find_plan_dir`, `source="heuristic"`, `_PIPE_STAGES`, and PID-only process associations before declaring the migration complete.

All unrelated state, control, memory, mouse, stable-order, dispatch-contract, token-budget, and currentness tests must continue to pass unchanged.

### Phase 6: Mirror synchronization and final gates

#### Step 6.1 — Synchronize canonical Fleet to the Claude projection

Target: `adapters/claude/tools/fleet/**`.

1. After canonical Fleet tests pass, synchronize the complete canonical tree with the repository's documented mirror command:

   ```bash
   rsync -a --delete --exclude='__pycache__' tools/fleet/ adapters/claude/tools/fleet/
   ```

2. Do not hand-edit mirror logic. New modules, fixtures, and tests must be byte-identical.
3. Run the mirror parity test before adaptation checks.

#### Step 6.2 — Run final verification in a no-provider environment

Use the Codex verification runner where shown so timeouts/results are durable. Commands are intentionally separated so a failure identifies its contract:

```bash
/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh verification-runner --timeout 360 -- \
  env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/fleet/tests -p 'test_*.py'

/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh verification-runner --timeout 180 -- \
  env PYTHONDONTWRITEBYTECODE=1 python3 utilities/compose_route.test.py

/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh verification-runner --timeout 240 -- \
  env PYTHONDONTWRITEBYTECODE=1 python3 utilities/capability_route.test.py

env PYTHONDONTWRITEBYTECODE=1 FLEET_TITLE_DISABLE=1 FLEET_DEMO=1 AGENT_DISPATCH_JOBS=/dev/null \
  python3 tools/fleet/fleet.py --once --view group

env PYTHONDONTWRITEBYTECODE=1 FLEET_TITLE_DISABLE=1 FLEET_DEMO=1 AGENT_DISPATCH_JOBS=/dev/null \
  python3 tools/fleet/fleet.py --once --view process

env PYTHONDONTWRITEBYTECODE=1 FLEET_TITLE_DISABLE=1 FLEET_DEMO=1 AGENT_DISPATCH_JOBS=/dev/null \
  python3 tools/fleet/fleet.py --json | python3 -m json.tool >/dev/null

env PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q tools/fleet adapters/claude/tools/fleet

env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tools.fleet.tests.test_mirror_parity

bash tools/adaptation-guard.test.sh
bash tools/check-adaptation-boundary.sh
```

For the CLI smoke commands, `FLEET_TITLE_DISABLE=1` is defense in depth; by contract `--once`/`--json` must not enter the scheduler at all. The hermetic fail-if-reached tests are the authoritative zero-provider evidence.

#### Step 6.3 — Final evidence package

The code-test/code-report stages must record:

- changed canonical and mirror files;
- exact commands, pass counts, and any skipped/unavailable runtime contracts;
- §4.12 acceptance row → test name mapping;
- proof that compose and canonical route compiler suites passed;
- `--once` group/process and public JSON smoke results;
- mirror byte parity and adaptation boundary results;
- explicit zero live/default/custom provider calls;
- the known spec-read-marker side-effect degradation;
- the required standard code QA assurance string: `plan-check:selected-independent-pass:final-verify`.

## Risks and mitigations

1. **Accidental dual stage authority.** Leaving `live_stage()` calls in collectors/renderers would recreate precedence drift. Mitigation: attach projections once, make consumers projection-only, and add fail-if-called tests around legacy resolution.
2. **Valid parallel work mistaken for ambiguity.** A naive cardinality check could reject two active siblings. Mitigation: distinguish multiple candidates for one leaf from multiple active nodes inside one validated route; only the former is ambiguous.
3. **Owner/conductor route guessed from rendering order.** Owners usually lack their own route tuple, so deleting renderer overrides without a parent-link resolver would erase valid DAG state. Mitigation: resolve only through `session_id/parent_sid` or `slug/parent_slug`, require one agreed sealed route/hash, and make conflicts machine-readable.
4. **PID reuse or partial child data mix.** PID-only matching can assign another process's title/context or sub-agent strip. Mitigation: exact `(pid, proc_start)` with no cwd fallback after an exact-identity mismatch, one atomic association result for all three fields, and the same exact map inside process cards.
5. **Artifact false positives or QA coupling.** The current fuzzy token/mtime fallback can choose an unrelated plan, and sharing its helper with QA can transfer stage semantics into QA. Mitigation: exact realpath-deduplicated cardinality across both roots plus a separately named QA-only resolver.
6. **Route metadata or label loss.** Existing route views omit `write_scope`, group breadcrumbs flatten topology, and loose labels could revive fixed semantics. Mitigation: preserve all sealed node metadata/topological levels, use the exact selected contract-or-node mapping, and test `research`/`claim-a` across every surface.
7. **Vertical density and narrow overflow.** A mandatory live `ctx —` row increases height. Mitigation: one compact row only, context token reservation, NOW-only clipping, no duplicate inline gauges, explicit process-row ownership, and fixed width tests at all four approved dimensions.
8. **Context compaction misclassified as stale/regression.** Comparing percentages rather than source order would reject valid decreases. Mitigation: compare selected/head sequence and freshness, never numeric direction; pin each harness's sequence source, newer-decrease, older-sequence, and expired-sample tests.
9. **OpenCode provider support writes live state, reuses the wrong cursor, or reads another session.** Mitigation: typed private refresh source, exact session ID, fixed compatible table order, SQLite `mode=ro`, integer rowid cursor plus `cursor_kind`, sidecar-only writes, and hermetic temp-DB metadata/byte checks.
10. **Quota bypass through direct worker entry.** `run_worker()` and spawned worker paths could diverge. Mitigation: retain shared lease acquisition at both ingress paths and test direct calls under a full slot/start budget.
11. **Mirror drift.** Parallel canonical/mirror edits can silently diverge. Mitigation: canonical-only logic changes, one final rsync owner, mirror test, adaptation boundary gate.
12. **Large change surface.** Projection, association, rendering, scheduler, and mirror files are coupled. Mitigation: keep the six phases dependency-ordered, land tests with each phase, and avoid touching compose/compiler logic that is already approved and passing.

## Verification and completion gate

Implementation is complete only when all of the following are true:

1. Every PRD §4.12 acceptance row has a named hermetic test and passes.
2. Session/DispatchJob projection parity, exact-over-artifact precedence, exact artifact-root cardinality, separate QA-only lookup, explicit-invalid refusal, deterministic contract-or-node `stage_label`, parent-link owner route agreement, arbitrary composed DAGs, and ambiguity refusal are proven.
3. One and only one context/NOW row is proven at wide@168, wide@120, narrow@100, and stack@60 in group/plain and beneath each live process job, including exact `(pid, proc_start)`, missing/stale/dead, and CJK overflow cases.
4. Context changes at 69/70/85 and a valid compaction decrease leave all orchestration/policy bytes unchanged; only expired, malformed, or selected-sequence-before-source-head evidence becomes unknown, with the private sequence/freshness contract proven for all three harnesses.
5. Title/NOW limits are exactly concurrency default 3/hard 4, starts default/hard 4 per rolling 60 seconds, and debounces 600/150 seconds; the OpenCode collector/scheduler/argv/CLI/`mode=ro` delta-reader/typed-sidecar path is proven end to end with zero DB writes.
6. No live provider invocation occurs in any test/snapshot/demo/width/projection/storm path.
7. Full Fleet, compose, canonical route compiler, once, JSON, syntax compile, mirror, adaptation guard, and adaptation boundary commands pass.
8. Standard code QA assurance is completed and reported as `plan-check:selected-independent-pass:final-verify`.
9. The final report truthfully records the owner-side spec-read-marker degradation and does not overclaim that side effect.

## Decision points

None. F-36 through F-39, the route evidence order, ambiguity behavior, UI coordinates, quota numbers, no-live-provider boundary, and mirror gate are already approved and locked. Any proposed deviation requires returning to the owner rather than silently choosing an alternative.

## Stage handoff evidence

- Route: `rt-dfec3aabe921b37f`, node `plan`, attempt `att-bd52297d13e27ec8636ccd3e0b8da7fa9b02393d4aafa38c`.
- Assigned contract: `code-plan`; mode `dev/refactor`; intensity `strong`; QA `standard`.
- Durable outputs: this file and sibling `checklist.md` under the canonical artifact root.
- Plan gate requirement: actionable file ownership, dependency order, full F-36..F-39 acceptance coverage, concrete verification commands, standard QA assurance, and unsupported marker detail are all present.

## Change history

### 2026-07-22 — merged review round 1 correction

- Made owner/conductor route discovery explicit through `session_id/parent_sid` and `slug/parent_slug`, with one-route/hash agreement and stable conflict ambiguity.
- Defined route-exact `stage_label` as the selected exact assigned contract when validated for that leaf, otherwise the opaque route node, with no semantic pipeline inference.
- Added `artifact_root` to exact-cardinality stage lookup and split QA into a separate QA-only resolver.
- Specified OpenCode refresh plumbing from collector source through scheduler, argv/CLI, `mode=ro` rowid delta reader, typed sidecar cursor, and zero-write tests.
- Assigned process-view detail rows to exact `(pid, proc_start)` job identities and made sequence/freshness evidence concrete.
- Added the superseded route/artifact/dispatch tests named by review while preserving the full v16 acceptance matrix and `plan-check:selected-independent-pass:final-verify` assurance.
