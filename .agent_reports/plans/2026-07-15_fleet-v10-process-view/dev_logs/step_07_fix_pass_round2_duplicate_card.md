# Step 7 — fix pass (code-test re-verification round 2, blocking: duplicate degrade card)

Input: `test_logs/verification_round_2.md` (code-test, read-only, mutation-tested). Defects 1-4
confirmed genuinely fixed (mutation M1/M2 catch real reverts); the round-1 diagnosis of the
duplicate degrade card as "pre-existing, out-of-scope, different job" was **wrong** — round 2
proved it is the same bug class as defect 1, at a second location, and a direct product of
defect 1's own fix (the record card is new, so the duplicate is new too).

## The one blocking fix — duplicate degrade card
**Root cause (confirmed by code-test, 1 field, same shape as defect 1)**: `render.py`'s
`_build_process_lines` computes `covered_slugs` (the depth-1 conductors to exclude from the
degrade pool because a real route card already represents them) by scanning **only live
`jobs`** for a route-carrying child's `parent_slug`. Once that child goes terminal
(`fleet-v10-plan`, `done`), `_scan_jobs_log` drops its row before a live `DispatchJob` exists for
it — `covered_slugs` stays empty — the conductor's bare slug re-enters the degrade pool — a
SECOND, contradicting "no route record" card renders 2 lines below the conductor's own real
record card. This is defect 1's exact assumption ("live jobs are enough") left unfixed at a
second call site — `route.resolve_records` was fixed, `_build_process_lines`'s `covered_slugs`
was not.

**Fix** (identical shape to defect 1 — 1 field carried through the same already-parsed pipe row,
0 new I/O):
- `tools/fleet/collectors/dispatch.py` `_scan_route_nodes` — each node's evidence dict now also
  carries `"parent"` (`meta.get("parent") or meta.get("parent_slug")` — the exact field
  `_scan_jobs_log` already reads for the same purpose on the live path).
- `tools/fleet/render.py`:
  - `_build_lines` — `_node_evidence` (already computed for route resolution) is now threaded
    into `_build_process_lines` as a new `node_evidence=` parameter (previously computed but
    never passed through to the process-view builder).
  - `_build_process_lines(..., node_evidence=None)` — `covered_slugs` now unions the live-job
    scan with a second pass over `node_evidence`'s `parent` fields, scoped to route_ids that
    already resolved into `route_views_by_id` (same guard the live-job branch already uses).

## Live measurement — the judgment criterion (coordinator's own words)
```
$ COLUMNS=120 python3 tools/fleet/fleet.py --once --view process
  ▸ [code·dev·standard] rt-1120bb39 — 4/4 nodes
  ▾ [code·dev·standard] rt-27f7bc9f — 0/4 nodes ⚠ failed node
    plan ✕ › execute ○ › test ○ › report ○
  ▾ [code·dev·standard] rt-41eef22d — 2/4 nodes
    ...
  ▸ [spec·update·standard] rt-70be9258 — 3/3 nodes
  ▾ [code·dev·standard] rt-9ff8199b — 0/4 nodes ⚠ failed node
    ...
```
`grep -c "fleet-v10-process-view — no route record"` → **0** (was present before the fix).
`grep -c "rt-27f7bc9f"` → **1** (the record card, exactly once). **Duplicate confirmed gone,
live, on this cycle's own record — the exact reproduction the coordinator specified as the
judgment criterion.**

## Regression test (M2-shaped, per instruction) + mutation-verified
`test_conductor_not_duplicated_as_degrade_card_when_route_child_is_terminal`
(`test_f30_process_view.py`, `RenderContentTest`) — production-realistic shape: `jobs=[conductor
only]` (the route-carrying child is terminal and therefore absent from live `jobs`, exactly like
the M2 pattern used for T3-5/T3-9b), route evidence carries `route_file` + `parent`. Asserts the
record card renders AND the conductor's bare slug never produces a second "no route record"
card.

**Mutation-verified** (reverted the `covered_slugs` union fix, workdir restored after, diff
confirmed identical): the test **fails** on the reverted code —
`AssertionError: 'no route record' unexpectedly found in ...`. Confirms real protection, not a
vacuous pass.

## Also fixed (🟢, code-test's mutation report: M3/M4 flagged FIXED but UNPROTECTED)
Both defect 3 and defect 4 (from the round-1 fix pass) were real fixes with **zero** test
coverage — reverting either left the full suite green. Added one lightweight test each,
mutation-verified against their own specific revert:
- `test_l1_elapsed_uses_the_hourglass_glyph_not_bare_clock` (M3) — calls `_route_card_l1`
  directly, asserts `"⏳15m"` present / the bare `"  15m"` shape absent. Mutation-verified:
  reverting `_route_card_l1`'s `"⏳"` back to `_CLOCK` fails this test
  (`'⏳15m' not found in '... — 1/4 nodes  15m'`).
- `test_demo_seeds_lab_setup_node_as_done` (M4) — calls `demo.collect()`, asserts
  `dispatch.collect.last_route_nodes[_LAB_RID]["setup"]["status"] == "done"`. Mutation-verified:
  removing the `_LAB_RID`/`setup` seed block from `demo.py` fails this test
  (`AssertionError: None != 'done'`).

Both mutations applied to a throwaway in-place edit + `diff` confirmed the workdir was restored
byte-identical before continuing (no dangling mutation left in the tree).

## Left untouched (explicit instruction, unchanged from round 1)
- `tracked_gate_evidence` / completion-gate pass evidence — honest gap, user-judgment item.
- Critic 🟡3 (degrade card visual weight) / 🟢4 (fold-affordance footer hint) — out of scope;
  note (per verification_round_2.md §11.4) that 🟡3's perceived severity naturally drops now
  that the duplicate-card case driving its "half the screen is degrade" framing is gone.

## Test results
- `python3 -m unittest discover -s tools/fleet/tests -t .` → **519 tests, OK**
  (516 prior + 3 new: the duplicate-card regression + the 2 mutation-coverage tests).
  **0 regressions.**
- Card-content overflow at 60/120/168 (live + demo) → **0**, re-verified after this pass.
- `--json` additive re-verified: `sessions/jobs/summary` unchanged, `route`/`governor` present,
  `gate_passed` absent.
- G3 static read-only gate → 0 lines, both canonical and mirror (4 files: `route.py`,
  `collectors/governor.py`, each tree).
- Mirror parity → `test_mirror_matches_canonical` OK (re-synced after this pass).
- tolerant-fallback / hash-verification path: unchanged — the `node_evidence`→`covered_slugs`
  fallback added here does not touch `route.load()`/hash verification at all (it is a
  display-layer degrade-pool exclusion, not a record-resolution path); the record-resolution
  `node_evidence` fallback added in round 1 (defect 1) was re-confirmed intact by the full
  suite, including `RouteLoadTest`'s adversarial-input coverage.

## Files changed this pass
- `tools/fleet/collectors/dispatch.py` — `_scan_route_nodes` evidence gains `"parent"`.
- `tools/fleet/render.py` — `_build_lines` threads `node_evidence` into `_build_process_lines`;
  `_build_process_lines` gains `node_evidence=None` param and unions it into `covered_slugs`.
- `tools/fleet/tests/test_f30_process_view.py` — 3 new tests (duplicate-card regression +
  2 mutation-coverage gap fills for M3/M4).
- All mirrored byte-identically to `adapters/claude/tools/fleet/`.
