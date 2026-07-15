# Step 1 — F-28a route record consumption

## Files
- `tools/fleet/route.py` (new) — `load()`/`route_hash()`/`node_order()`/`resolve_records()`/
  `build_views()`/`collect_views()`/`summary()`/`clear_cache()`. Zero writes (no
  `open(...,"w")`/`write_text`/`os.replace`/`.write(` anywhere in the file).
- `tools/fleet/model.py` — `DispatchJob` +4 fields: `route_file`/`route_id`/`route_hash`/
  `route_node` (all `Optional[str] = None`, additive).
- `tools/fleet/collectors/dispatch.py` —
  - `_iso_to_epoch()` (new, sibling of `_iso_elapsed_min`) — returns epoch float, not
    pre-computed elapsed, so `route.build_views`'s `now` argument does the elapsed math (purity).
  - `_scan_route_nodes(paths)` (new) — rereads jobs.log (same file, second pass — precedent:
    `_jobs_log_fields`), keeps TERMINAL rows unlike `_scan_jobs_log`, last-occurrence-wins per
    (route_id, route_node).
  - `_scan_processes` (proc jobs): attaches `route_file`/`route_id`/`route_node` from
    `AGENT_ROUTE_FILE`/`AGENT_ROUTE_ID`/`AGENT_ROUTE_NODE` env (confirmed real names,
    `adapters/claude/bin/dispatch-headless.py:749-751`). `route_hash` stays `None` — that env
    var is not exported; integrity still rests on the record's own recomputed hash.
  - `_scan_jobs_log`: attaches all 4 fields from the pipe (`route_file=`/`route_id=`/
    `route_hash=`/`route_node=` — `_parse_pipe_meta` already parsed these, no changes needed there).
  - `collect()`: stashes `collect.last_route_nodes = _scan_route_nodes(paths)` (module attribute,
    `last_malformed` precedent — no return-signature change).
- `tools/fleet/fleet.py` — `_snapshot_json` gains a `route` key via `_collect_route(jobs)`
  (best-effort try/except, `mem` precedent). Reads `dispatch.collect.last_route_nodes` and calls
  `route.collect_views()` + `route.summary()`.
- `tools/fleet/tests/test_f28_route.py` (new, 19 tests, T1-1..T1-17 plus 2 extra build_views cases).
- `tools/fleet/tests/fixtures/route/` (new) — `real_claude_staged.json` (copy of the live record
  compiled for this cycle), `real_codex_staged.json` (copy of `/tmp/agent-note-d1-route.json`,
  since evicted), `synth_broken_hash.json`, `synth_bad_schema.json`, `synth_parallel_lab.json`
  (3-way fan-out + fan-in, hash/id generated via `route.route_hash()`, never hand-written),
  `jobs_route.log` (4 real pipe rows, `route_file=` rewritten to a `{FIXDIR}` placeholder for two
  of them), `README.md` (fixture provenance).

## Design decisions beyond the plan skeleton (filled gaps, documented here per plan's own
"§3.1 skeleton is loose pseudocode" acknowledgment)
- `build_views(jobs, node_evidence, records, now)` takes `records` (`{route_id: record}`)
  as an explicit 3rd argument so it stays genuinely I/O-free (pure) — the plan's skeleton
  omitted this arg but its own prose (§3.3: "순수 함수 — 파일 I/O도 시계도 만지지 않는다")
  requires the loaded record to arrive from outside. `resolve_records(jobs)` is the one impure
  function that calls `load()`; `collect_views(jobs, node_evidence, now=None)` is the
  convenience wrapper fleet.py/render.py actually call.
- A route with **no live job** (every node already done/failed, so `_scan_jobs_log` dropped all
  its rows) still produces a view as long as `records` or `node_evidence` name its route_id —
  this is load-bearing for Step 3's "완료 route 1행 접힘" card. Caught a real test-isolation bug
  from this (a leftover `dispatch.collect.last_route_nodes` module stash leaking between tests
  that call `fleet._snapshot_json` directly without a fresh `dispatch.collect()`) — fixed by
  resetting the stash in test setUp/tearDown, not by weakening the production behavior.
- `route.py`'s `capability` field is left with its raw `autopilot-` prefix in `summary()`/views;
  the prefix-strip (`_strip_autopilot_prefix`, dispatch.py:68) is a render-layer concern (Step 3
  card L1), not a route.py concern, to avoid a route.py → collectors.dispatch import.

## Test results
- `python3 -m unittest tools.fleet.tests.test_f28_route -v` → 19/19 OK.
- `python3 -m unittest discover -s tools/fleet/tests -t .` → **487 tests, 1 failure** (expected:
  `test_mirror_parity` — mirror resync deferred to Step 5 per plan). 468 baseline + 19 new, **0
  regressions** among the pre-existing 468.

## Risk noted (plan §3.6)
- `_scan_route_nodes` rereads jobs.log unconditionally on every `collect()` tick (no gate on
  "any job has a route_id" the way the mode/profile backfill gates its extra `ps` scan). This is
  a second `open()`+`read()` of the same (typically small, hundreds-of-lines) file per tick —
  acceptable per the plan's own risk note (§3.6: "jobs.log는 수백 행 규모의 로컬 파일... 무시할
  만하다"), flagged here for Step 5 review rather than silently accepted.
