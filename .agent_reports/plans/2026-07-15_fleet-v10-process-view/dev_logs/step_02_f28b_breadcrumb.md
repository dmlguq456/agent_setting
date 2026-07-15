# Step 2 — F-28b route-aware breadcrumb

## Files
- `tools/fleet/render.py`:
  - `_route_stage_segs(route_seq, working, max_width)` (new) — renders a `[(node_id, state), ...]`
    list (state ∈ active/done/failed/pending, route.py §3.3's single judge) into breadcrumb
    segments, reusing `_drop_past_stages` unmodified (SD-F2 fold behavior, no new width logic).
  - `_stage_segs(..., route_seq=None)` — `route_seq is not None` short-circuits straight to
    `_route_stage_segs`, bypassing `_PIPE_STAGES.get(key)` entirely. Default `None` = 100%
    pre-v10 behavior (T2-1 pins this byte-for-byte).
  - `_dispatch_stage_segs(..., route_seq=None)` — depth≥2 branch is UNCHANGED and never even
    looks at `route_seq` (P0-1 invariant); depth-1 with a non-empty `route_seq` takes the route
    path over the `_STAGE_ROLE` role-label-prefix path.
  - `_dispatch_row`/`_dispatch_row_2line`/`_dispatch_row_stack` — all three gained a `route_seq`
    kwarg (default `None`), threaded straight to `_dispatch_stage_segs`.
  - `_build_lines` — right after the `_SELECTABLE = []` reset (the same injection point Step 3
    uses for the process-view branch), best-effort resolves every route referenced by `jobs`
    once per build into `_route_views_by_id = {route_id: view}` via
    `route.collect_views(jobs, dispatch.collect.last_route_nodes)`. Wrapped in try/except — a
    route.py failure degrades to "no route data this tick", never breaks the group view.
  - `_conductor_stage_override(job)` (per-group closure) — now checks a route-carrying ACTIVE
    depth-2 child FIRST (`k.route_node`) before falling back to the pre-existing
    `_STAGE_ROLE`-label lookup (plan §4.2: "route_node 우선, 없으면 기존 _STAGE_ROLE 폴백").
  - `_conductor_route_seq(job)` (new, same closure scope) — finds a depth-2 child's `route_id`
    (the depth-1 conductor row itself rarely carries one — dispatch.py attaches the route
    env/pipe link to the STAGE WORKER, not the top job), looks it up in `_route_views_by_id`,
    and returns its flattened `[(node_id, state), ...]` node list (already in level order —
    `route.py`'s `_record_view` builds `nodes` level-by-level).
  - `_emit_dispatch_tree` — computes `route_seq = _conductor_route_seq(job)` alongside the
    existing `stage_override` computation, passes it to whichever row-builder is in play.
- `tools/fleet/tests/test_f28_breadcrumb.py` (new, 6 tests: T2-1 through T2-6).

## `_PIPE_STAGES` / `_STAGE_ZONE_MAX` — untouched, as the plan mandates
- `_PIPE_STAGES` dict itself: zero edits — it remains the sole path for record-less jobs.
- `_STAGE_ZONE_MAX = 30`: zero edits, zero new width constants. `_drop_past_stages` is reused
  unmodified — verified in T2-2 that a 4-node route breadcrumb folds its PAST (done) node under
  the same 30-column budget a 4-stage `_PIPE_STAGES` breadcrumb would.

## Test results
- `python3 -m unittest tools.fleet.tests.test_f28_breadcrumb -v` → 6/6 OK.
- `python3 -m unittest discover -s tools/fleet/tests -t .` → **493 tests, 1 failure** (expected
  mirror-parity, deferred to Step 5). 487 (Step 1 total) + 6 new, **0 regressions**.

## Note on T2-2's actual assertion shape
Initial draft asserted the literal substring `"plan✓"` survives in the rendered breadcrumb text
— it does not, because `_STAGE_ZONE_MAX`'s existing SD-F2 fold correctly drops the past ("plan✓")
stage once the combined width of `plan✓ › execute › test › report` exceeds 30 columns, exactly as
it would for a 4-stage `_PIPE_STAGES` breadcrumb. This is CORRECT behavior, not a bug — the test
was adjusted to assert the surviving stages (`execute`/`test`/`report`, using the record's own
node ids rather than `_PIPE_STAGES`'s `exec` abbreviation) plus a direct, width-independent check
on `route.build_views()`'s own node-state output (`plan` state == `done`).
