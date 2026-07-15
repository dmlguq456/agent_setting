# Step 3 — F-30 process view

## Files
- `tools/fleet/render.py` — the bulk of this step:
  - `_PROCESS_VIEW`/`set_process_view()`, `_ROUTE_FOLD`/`_FOLDABLE` globals.
  - `p`/`P` key in `_handle_base_key` (orthogonal to `w`, unchanged per prd.md:305).
  - `_pulse_segs(sessions, jobs)` (extracted, byte-identical, from `_build_lines`'s inline
    pulse-row block) — shared between group view and process view header (§5.2's "공통 헤더
    헬퍼로 재사용", applied to the pulse row specifically; malformed/mem-summary lines are
    duplicated as single-line calls rather than factored, see "Scope decisions" below).
  - `_route_node_text`, `_route_card_l2`, `_route_job_row`, `_route_card_l1`, `_route_card`,
    `_degrade_candidates`, `_degrade_card`, `_build_process_lines` (all new) — the card-building
    pipeline.
  - `_build_lines` — one branch point, right after `_SELECTABLE = []` AND the route-views
    resolution both views need (§5.2's mandated single injection point).
  - `_FOLD_ROWS` global + `_draw`'s row loop (checked BEFORE the `_TOGGLE_ROWS` substring test,
    structurally guaranteeing I7/§5.4 B2's disjointness) + `_handle_mouse` rung 3 (between the
    `a`-toggle rung and the F-27 row-click rung).
  - `_footer_segs` — `p process`/`p group` hint, gated at `_PROCESS_HINT_MIN_WIDTH = 80` (own
    threshold, not reusing `_MOUSE_HINT_MIN_WIDTH` — a different capability, no reason to couple
    the two).
- `tools/fleet/fleet.py` — `--view {group,process}` (P3, additive) + `FLEET_VIEW` env fallback
  (plan §9 note 1's reduction path), both routed through the SAME `render.set_process_view()`
  the `p` key uses (single decision path, F-27 precedent extended to F-30).
- `tools/fleet/demo.py` — 3 route-carrying jobs (a resolved-record card via a fabricated
  `demo_card.json` fixture — see "demo route id" below — a fan-out/fan-in parallel card with a
  FAILED branch via `synth_parallel_lab.json`, and a record-less degrade job) + 1
  subagent-bearing session (pid-joined to the resolved-record card's active node).
- `tools/fleet/tests/fixtures/route/demo_card.json` (new) — see "demo route id" below.
- `tools/fleet/tests/test_f30_process_view.py` (new, 15 tests: T3-1..T3-14 plus T3-9b).

## Demo route id — a fabricated fixture, not the real captured one (bug found + fixed)
The plan's real `real_claude_staged.json` fixture (route_id `rt-27f7bc9ff152ba13`) is, quite
literally, THIS execute cycle's own real route record — reusing it for `demo.py` meant a live
(non-isolated) `--demo` run merges demo data with the SAME route_id's REAL evidence from the
live `.dispatch/jobs.log` (this cycle's actual `plan` stage row, marked `note=dead-plan-done`).
That collided into the demo card showing `plan ✕` instead of the intended `plan ✓` — confusing,
not wrong (the real evidence read correctly), but not what a demo fixture should depend on.
Fixed by generating `demo_card.json`: `real_claude_staged.json` with fabricated `cwd`/
`source_commit`/`registry_digest` (content-addressed hash, guaranteed not to collide with any
real record) — route_id `rt-2f5c79f591479409`.

## Bug found + fixed: conductor double-listed as its own degrade card
A depth-1 conductor whose depth-2 CHILD carries the resolved `route_id` (§3.2 — the route
env/pipe link attaches to the stage worker, not the top job) was ALSO matching
`_degrade_candidates`'s filter (which only checks the JOB'S OWN `route_id`, always `None` on a
conductor) — every route-carrying pipeline showed up TWICE: once as its real card, once as a
spurious "no route record" card for the bare conductor slug. Fixed by computing `covered_slugs`
(every `parent_slug` whose CHILD resolved into `route_views_by_id`) in `_build_process_lines`
and excluding them from `_degrade_candidates`.

## Bug found + fixed: card-row width overflow at 60 columns
Initial L1 (capability/mode/intensity tag + route_id + progress) and the active-node job row
(`└▸🚀 <slug> ...`) both overflowed 60 columns with demo data. Fixed:
- `_route_job_row(job, max_width=...)` — the slug is the one variable-width field; it clips via
  `_clip_w` first, all fixed-shape fields (harness/model/effort/elapsed) survive.
- `_route_card_l1(...)` — a `_prompt_variants`-style pick-first-fit ladder (§5.5's explicit
  instruction to reuse that idiom): drops `effective_intensity`, then `capability_mode`, then
  the elapsed/failed-node suffixes, keeping `capability` + route_id + progress as the
  never-dropped floor.
- `_degrade_card`'s slug also clips via `_clip_w` at narrow widths.
- Verified via a direct `_dw()`-sum script at 60/120/168 (see `_internal/` capture note below) —
  **0 overflow in every NEW process-view line**. The shared pulse/usage/legend header rows
  (`_pulse_segs` and friends) overflow at 60 columns in BOTH the group view and the process
  view — this is PRE-EXISTING behavior (verified: identical overflow present in the unmodified
  group view against the same demo data), not a v10 regression, and out of this step's scope.

## `_WIDE` glyph check (§5.5, explicit plan instruction)
Checked: `✓`(U+2713) `✕`(U+2715) `●`(U+25CF) `○`(U+25CB) `▸`(U+25B8) `▾`(U+25BE) `⚠`(U+26A0) all
fall OUTSIDE every wide range `_cw()` tests (CJK/Hangul/fullwidth/emoji: 0x1100-0x115F,
0x2E80-0xA4CF, 0xAC00-0xD7A3, 0xF900-0xFAFF, 0xFF00-0xFF60, 0xFFE0-0xFFE6, 0x1F000-0x1FAFF) — all
render as 1 cell, matching the codebase's EXISTING treatment of `✓`/`●`/`○` in `_LIVE_GLYPH`
(unchanged there). No `_WIDE` edit needed.

## Scope decisions (documented, not hidden)
- Malformed-count and mem-summary header lines are duplicated (one line each) in
  `_build_process_lines` rather than factored into a shared helper — they were already
  single-line, low-risk to duplicate, and factoring them would have meant touching
  `_build_lines`'s existing (working, tested) header assembly for marginal benefit. The pulse
  row (`_pulse_segs`) WAS factored — it is the row every group-view/process-view screenshot
  reader looks at first, and it was the one with real duplicate-drift risk (session/job counts).
- The `a`-toggle detail line for `tracked_gate_evidence` (§5.3, prd.md:310) shows completion
  **gate names** only (`gates: code-plan, code-execute, ...`) — not the full
  `tracked_gate_evidence` object shape from the raw record (spec_read/drift_verdict/
  workflow_mode/artifact_guard). The raw record fields are compile-time provenance, not
  something `route.py`'s summarized view carries at all (§3.4: "route는 요약이다... record
  원문은 싣지 않는다") — showing gate names is the faithful summarized equivalent.
- F-27 kill capability from the process view is available ONLY for a route's active-node job row
  (via `_SELECTABLE`/`_CLICK_ROWS`, identical mechanism to the group view) — a degrade card has
  no job-row entry (its L1 IS the fold target, and giving the same row two conflicting meanings
  would violate I7). A user who needs to kill a record-less job can still do so from the group
  view; this is a known, deliberate scope narrowing, not an oversight.

## Test results
- `python3 -m unittest tools.fleet.tests.test_f30_process_view -v` → 15/15 OK.
- `python3 -m unittest discover -s tools/fleet/tests -t .` → **508 tests, 1 failure** (expected
  mirror-parity, deferred to Step 5). 493 (Step 2 total) + 15 new, **0 regressions**.
- Manual 3-width smoke (`COLUMNS={60,120,168} FLEET_DEMO=1 python3 tools/fleet/fleet.py --once
  --view process`) — all 3 render cleanly; card content overflow 0 (verified via `_dw()` sum
  script, see above).
- `python3 tools/fleet/fleet.py --once --view process` (no demo) → renders "no active route"
  honestly on this otherwise-idle terminal tick — T3-14's exact scenario, confirmed live too.

## Risk / follow-up for Step 5
- The 3-width demo captures above were produced with `python3 tools/fleet/fleet.py --once --view
  process` piped through a script, not curses-rendered — Step 5's V2/V3 (design critic capture)
  should re-verify visually before the critic review, in case ANSI/curses color codes shift any
  cell width the plain-text `_dw()` check cannot see.
