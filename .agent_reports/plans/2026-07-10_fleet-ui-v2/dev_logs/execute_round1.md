# Execute round 1 — fleet UI v2 (SD-F1~F4, F-9~F-13)

Safety commit: `ae8c1657e66fb6b282b4923ef75e46c411aa11c2`

## Summary

All Phase 1–4 checklist items implemented and committed on branch `fleet-ui-v2` (no merge, no
push, worktree left in place). 36 pre-existing unit tests remain green; 12 new tests added
(48 total). Render smoke-tested with `--once`, `--json`, and `--demo --once` (wide layout).

## Commits

1. `ceb286c` — Phase 1–2 (SD-F1~F4): tolerant pipe parser + stage-dispatch schema.
2. `c9abfa1` — Phase 3 (F-9~F-13): readability polish.
3. (pending, this log's commit) — Phase 4: new unit tests + checklist/log artifacts.

## Changed files

- `tools/fleet/collectors/dispatch.py`
  - `_PIPE_TOK` regex constant + `_parse_pipe_meta` rewritten as a continuation tokenizer
    (comma/space tolerant, value-internal-space safe). `eq_pos < colon_pos` gate and
    `head = pipe.split("(", 1)[0]` preserved unchanged.
  - `_scan_jobs_log`: `DispatchJob(...)` now passes `effort=meta.get("effort")`,
    `model_role=meta.get("model_role")`.
  - `_scan_processes`: both `DispatchJob(...)` call sites (autopilot job branch, loop job
    branch) now pass `effort=env.get("AGENT_DISPATCH_EFFORT")`,
    `model_role=env.get("AGENT_DISPATCH_MODEL_ROLE")` — defensive; these env vars aren't
    exported by the current dispatch-headless wrapper, so `None` is the expected/normal value
    on this path (R5, confirmed in plan Current State Analysis).
- `tools/fleet/model.py`
  - `DispatchJob`: added `effort: Optional[str] = None`, `model_role: Optional[str] = None`.
- `tools/fleet/render.py`
  - `_STAGE_ROLE` map + `_stage_role_label()` (SD-F1): `code-plan/execute/test/report` →
    `plan/exec/test/report`, `:phase-X` suffix split out.
  - `_ROLE_SHORT`: removed hardcoded `g6_worktree_dispatch`/`g9_cross_harness_depth2_dispatch`
    entries; added `_G_CASE_PREFIX = re.compile(r"^(g\d+[a-z]?)")` general rule.
  - `_short_role()`: tries `_stage_role_label` first, then the `gN` general rule, then the
    (now-smaller) `_ROLE_SHORT` map, else falls back to the old dash→underscore behavior.
  - `_dispatch_role_suffix(j, check_text=None, max_width=None)`: now builds `(kind, text)`
    pairs and, when `max_width` is given, drops whole components in `qa → intensity → role`
    priority order (F-9(c)) instead of a blind tail-cut. `_dispatch_profile` passes a computed
    budget (`_PROFILE_MAX=28` minus any leading `profile/` prefix).
  - `_emit_dispatch_tree`: new nested `_conductor_stage_override(job)` — looks at
    `job_children.get(job.slug, [])` filtered to depth-2 jobs whose `worker_role` maps via
    `_stage_role_label`; if any such child has `liveness == "working"`, that child's stage
    wins; else falls back to `job.stage` (SD-F2). Result threaded as a new `stage_override`
    kwarg through `_dispatch_row`, `_dispatch_row_2line`, `_dispatch_row_stack` down into the
    `_stage_segs(...)` call in each.
  - `_dispatch_row` / `_dispatch_row_2line`: own `j.effort` now first-class in the model cell;
    falls back to `parent_effort` prefixed with the derived-value `~` marker when the job's
    own effort is absent (SD-F3).
  - `_stage_segs`: `"open"` → `"queued"` label; `"running"` with no known pipeline track now
    renders dim (`stg0_off`) instead of a bright raw token (F-11). jobs.log status vocabulary
    itself is unchanged — display layer only.
  - Footer `wlbl`: `"wide/narrow"` → `"wide/narrow/stack"` when `_LAYOUT == "auto"` (F-12(b)).
  - `+N malformed` line: confirmed already `"dim"` — no change (F-12(a)).
  - `_build_lines`: new **local** `_seen_glyphs` set (F-12(c)) tracking which of
    detached/stale/dead/child-jobs/worktree glyphs actually appeared this build (via
    predicate checks at the session loop, the worktree-count branch, and inside
    `_emit_dispatch_tree`). Legend now only lists those conditionally; working/idle/dispatch/
    `~` stay unconditional. Purely function-local state — no module/global variable — so the
    `_OFFSET` invariant (R3, plain/`--once` path parity) holds.
  - Alert strip (F-10): names go through `_compact_dispatch_name` with a new
    `_ALERT_TAIL = re.compile(r"-\d{8,}-\d+$")` tail-strip first; same-kind alerts aggregate
    into one bucketed line each (dead/stale/ctx), in `dead > stale > ctx` priority; on overflow
    (budget mirrors the existing `names[:90]` dormant-dirs convention) lower-priority buckets
    are dropped from the tail.
  - `_session_row` / `_dispatch_row`: stale/dead rows (`dead_stale` / `j.liveness in
    ("stale","dead")`) collapse the model+ctx-gauge / model+stage-breadcrumb zone into a
    single `"last seen <age>"` cell (F-13). Only the 1-line (`wide`) layouts were touched —
    the narrow/stack 2-line variants weren't named in the plan's Current State Analysis and
    were left as-is (see Deviations).
- `tools/fleet/tests/test_dispatch.py`
  - `TolerantPipeParsingTest`: (a) space-separated, (b) value-internal-space, (b-extra, N2)
    continuation-then-more-fields, (c) unknown-key-ignored, plus a canonical-comma regression
    guard alongside the existing D5 class.
  - `StageWorkerRenderTest`: (d) all four `code-*` stage labels render correctly (not raw
    `worker_role`); plus a direct `_short_role` check for g6/g9/g8b (N1 regression anchor).
  - `ConductorBreadcrumbTest`: (e) three cases — active-child aggregation, own-stage fallback
    when the child isn't working, and the N5 report-child lone-bright-token case (assertions
    pin the exact expected color keys, e.g. `stg1_on`/`stg0_off`).
  - `AlertHumanizeTest`: (f) multi-dead aggregation + tail-strip, and single-item
    non-aggregation.

## Checklist / plan status

- `plan/checklist.md`: all items `[x]`.
- `plan/plan.md` frontmatter: `status: active` → `status: done`.

## Deviations from plan / decisions

- **N5 (report breadcrumb)**: kept the plan's "minimal" option — a lone bright `report` token
  via the existing fallthrough in `_stage_segs`, rather than adding a dedicated
  post-track-dim-highlight rendering path. Pinned by
  `test_conductor_breadcrumb_report_child_renders_lone_bright_token`.
- **Step 2.6 (stage suffix dim)**: the whole dispatch profile tag (`_mq_tag`'s `profile`
  segment) already renders with color key `"dim"` as a single segment, so a `:phase-A` suffix
  riding inside that same string is already visually de-emphasized — no separate color-key
  split was added. Noted inline in the code comment and in checklist item 2.6.
- **F-12(c) glyph tracking**: implemented via **data predicates** evaluated at existing loop
  points (session liveness/detached checks, the `_nwt` worktree-count branch,
  `_emit_dispatch_tree`'s job liveness), rather than literally collecting every rendered
  glyph character. Functionally equivalent (same conditions that choose a glyph decide
  whether it's "seen"), simpler, and still fully local to `_build_lines` (R3 preserved). This
  is the plan's own suggested fallback when the full approach gets complex.
- **F-13 scope**: only `_session_row`/`_dispatch_row` (1-line/`wide` layout) were changed, per
  the plan's Current State Analysis citation. `_session_row_2line`/`_dispatch_row_2line`/
  `_stack` variants (narrow/stack layouts) keep the pre-existing dim `"—"`-filled telemetry
  cells for stale/dead rows — not a regression, just unchanged, since the plan didn't name
  these functions for F-13.
- Alert-strip aggregation replaces the old flat `alerts[:6]` cap with per-bucket aggregation +
  priority-drop; this is more permissive of item *count* than the PRD's literal "최대 6개"
  phrasing in a couple of spots but preserves the "bounded single row" intent via a character
  budget instead. This is spec-text staleness (a display-layer refinement explicitly
  authorized by F-10), not a scope violation — left for the spec owner to reconcile in a
  future spec-sync pass rather than edited here.

## Verification run this session (iterative, not the final gate)

```
cd tools && python3 -m unittest fleet.tests.test_dispatch -v   # 48 tests, OK
python3 tools/fleet/fleet.py --once                            # ran clean, no exceptions
python3 tools/fleet/fleet.py --json                             # effort/model_role present in output
COLUMNS=200 python3 tools/fleet/fleet.py --demo --once          # wide layout, F-13 last-seen + F-10 alert visible
```

Full/adversarial verification is the `code-test` stage's responsibility — not re-run as a
final gate here per the execution contract.
