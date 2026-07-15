# Step 6 — fix pass (code-test YELLOW → defects 1-4)

Input: `test_logs/verification.md` + `test_logs/design_review_round_1.md` (code-test, read-only,
YELLOW). All 4 requested defects addressed; nothing outside the explicit list touched
(`tracked_gate_evidence`/completion-gate-pass evidence left exactly as disclosed, per
instruction).

## Defect 1 (blocking) — FIXED, live-verified
**Root cause (1 field, per verification.md §10)**: `_scan_route_nodes` (dispatch.py) kept
terminal jobs.log rows as node evidence but never carried `route_file` in that evidence, and
`route.resolve_records(jobs)` only ever looked at LIVE `jobs` for `route_file`. Once every
route-carrying row for a route_id went terminal (done/killed/cancelled — dropped by
`_scan_jobs_log` before classification), no live job remembered where the record lived, so a
perfectly valid, hash-verified record silently degraded to a heuristic "no route record" card.

**Fix**:
- `tools/fleet/collectors/dispatch.py` `_scan_route_nodes` — each node's evidence dict now also
  carries `route_file`/`route_hash` (from the same pipe row already being parsed — no new I/O).
- `tools/fleet/route.py` `resolve_records(jobs, node_evidence=None)` — new second parameter;
  after exhausting `jobs`, falls back to any node's `route_file`/`route_hash` in `node_evidence`
  for a route_id not yet resolved. `collect_views` passes `node_evidence` through.

**Live measurement (the judgment criterion, code-test's own words)** — this cycle's own record,
before vs after:
```
BEFORE (code-test's repro):
  ▾ [code·dev] fleet-v10-process-view — no route record
    plan › exec › test

AFTER (this fix, live, COLUMNS=120 --view process):
  ▾ [code·dev·standard] rt-27f7bc9f — 0/4 nodes ⚠ failed node
    plan ✕ › execute ○ › test ○ › report ○
```
`--json` for `rt-27f7bc9ff152ba13` now: `"source": "record", "capability": "autopilot-code",
"nodes"` has all 4 (plan/execute/test/report) with real state (`plan` = `failed`, correctly
reading the live registry's `note=dead-plan-done` per §3.3.1 — an honest read of this cycle's
actual terminated-plan-stage state, not a fabricated pass). **Defect 1 confirmed fixed live.**

**Test fix (code-test's explicit instruction)**: T3-5 and T3-9b previously injected a
`liveness="idle"` depth-2 job to represent a "done" stage — code-test correctly identified this
as a state production can never produce (`_scan_jobs_log` drops terminal rows before a
`DispatchJob` is ever created for them). Both rewritten to `jobs=[]` + `node_evidence` carrying
`route_file` — the actual production shape of "every node done, zero live jobs remaining".
Added `test_t1_13b_terminal_only_route_still_resolves_to_a_record_not_heuristic` (route.py-level,
using the existing `jobs_route.log` fixture's `v93-reading-face-d1-test-r6` row, which is
already `done` in the fixture and therefore has zero live jobs for its route_id) — pins the
exact defect shape with the existing fixture, no new fixture needed.

## Defect 2 (dependent on 1) — FIXED, live-verified
"완료 route 1행 접힘" is now reachable: live capture above shows `▸ [code·dev·standard]
rt-1120bb39 — 4/4 nodes` and `▸ [spec·update·standard] rt-70be9258 — 3/3 nodes`, both correctly
1-line-folded (▸ glyph, all-done routes with no live job) — this was structurally impossible
before defect 1's fix (an all-done route never produced a "record" view at all). No separate
code change beyond defect 1's fix; confirmed working as a consequence.

## Defect 3 (critic 🟡1) — FIXED
`demo.py:_seed_route_evidence()` seeded `_DEMO_CARD_RID`'s `plan` node but never
`_LAB_RID`'s `setup` node, so the parallel-fan-out demo card drew `setup ○` (pending) with
`active`/`failed` DEPENDENTS already running — a logically impossible DAG state, on F-30's own
marquee demo screen. Fixed: `_seed_route_evidence` now also seeds `_LAB_RID`'s `setup` as done.
Live demo capture after fix: `setup ✓10m` with `eval-asr ●`/`eval-sep ✕`/`eval-vad ○` beneath it
(consistent — a done parent can have active/failed/pending children) and progress reads `1/6
nodes` (was `0/6 nodes`).

## Defect 4 (spec-letter deviation, critic 🟡2) — FIXED
prd.md:307 specifies L1 as `<n/m nodes> ⏳<경과>`; the implementation used the bare `_CLOCK`
convention (render.py:540, correct for the SESSION/DISPATCH GRID rows it was designed for, but
wrong here) — no `⏳` glyph, and critic noted the resulting `1/4 nodes  15m` read as the elapsed
number being mistaken for part of the node count, while the SAME card's child job row already
used `⏳8m`. Fixed `_route_card_l1`: replaced `(_CLOCK, "dim")` with a literal `"⏳"` segment,
matching `_route_job_row`'s own established convention. Live: `rt-2f5c79f5 — 1/4 nodes  ⏳15m`
now matches its own child row's `⏳8m` — both use the same glyph, no reader ambiguity. `⏳` is
already in `_WIDE` (render.py:2510, pre-existing) — no width-table change needed; the L1 ladder's
own `_dw`-based fit check absorbs the extra 2-cell glyph automatically.

## Left untouched (explicit instruction)
- `tracked_gate_evidence` — no implementation attempted; the honest disclosure in
  `dev_logs/step_03_f30_process_view.md` stands, left as a user-judgment item.
- Completion-gate PASS evidence — remains an honest `—` (no `gate_passed` key anywhere),
  per the plan's own pre-committed §3.3.1 decision. Re-verified absent in `--json` post-fix.
- Critic 🟡3 (degrade card visual weight) and 🟢4 (fold-affordance footer hint) — NOT in the
  coordinator's explicit defect list (only defects 1-4 were requested); left as-is.

## Test results
- `python3 -m unittest discover -s tools/fleet/tests -t .` → **516 tests, OK**
  (515 prior + 1 new: `test_t1_13b_terminal_only_route_still_resolves_to_a_record_not_heuristic`).
  **0 regressions.**
- G3 static read-only gate → 0 lines, both trees.
- `--json` additive re-verified: `sessions/jobs/summary` unchanged, `route`/`governor` present,
  `gate_passed` absent.
- Mirror parity → `test_mirror_matches_canonical` OK (re-synced after the fixes).
- Card-content overflow at 60/120/168 → 0 (re-verified after the `⏳` glyph addition).

## Files changed this pass
- `tools/fleet/collectors/dispatch.py` — `_scan_route_nodes` evidence gains `route_file`/`route_hash`.
- `tools/fleet/route.py` — `resolve_records(jobs, node_evidence=None)` signature + fallback logic; `collect_views` updated; module docstring contract updated.
- `tools/fleet/render.py` — `_route_card_l1` uses `"⏳"` instead of `_CLOCK`.
- `tools/fleet/demo.py` — `_seed_route_evidence` also seeds `_LAB_RID`'s `setup` node; `_DEMO_CARD_RID`'s `plan` evidence gains `route_file`/`route_hash` for consistency with the defect-1 fix shape.
- `tools/fleet/tests/test_f28_route.py` — new `test_t1_13b_terminal_only_route_still_resolves_to_a_record_not_heuristic`.
- `tools/fleet/tests/test_f30_process_view.py` — `test_t3_5_*`/`test_t3_9b_*` rewritten to the production-realistic `jobs=[]` + terminal-evidence shape.
- All mirrored byte-identically to `adapters/claude/tools/fleet/`.
