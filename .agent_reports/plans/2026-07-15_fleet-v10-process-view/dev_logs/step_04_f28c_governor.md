# Step 4 — F-28c (split judgment, plan §6/P2)

## 4a — governor lease (implemented)
- `tools/fleet/collectors/governor.py` (new) — `collect(root=None)` → `{"active": n, "cap": m,
  "classes": {cls: n, ...}} | None`. Read-only + mtime/size cache (`route.py`/`_scan_route_nodes`
  precedent). Path resolution mirrors `utilities/model-worker-governor.py:24-33 default_root()`
  MINUS its `artifact-root.sh` subprocess fallback (module docstring explains why — no
  subprocess spawn per tick; the env-var and `$AGENT_ARTIFACT_ROOT` branches cover every real
  dispatch-broker launch path already).
- ★ **Dead-lease filter, in memory only** — governor prunes dead leases (PID-reuse-guarded via
  `process_starttime(pid) == lease["starttime"]`) only at WRITE time
  (`model-worker-governor.py:80-84`). A read-only consumer never gets that pruning for free, so
  `governor.collect()` re-applies the exact same judgment (`procscan.read_proc_start(pid) ==
  str(lease["starttime"])`) in memory, every read — verified by
  `test_dead_lease_never_write_state_json_but_excluded_from_count` (asserts both the count AND
  that `state.json`'s bytes are byte-identical before/after the read).
- `tools/fleet/render.py` — `_governor_segs()` (pulse-adjacent 1-line, healthy-quiet below half
  cap — `_GOVERNOR_QUIET_FRACTION = 0.5`), wired into both `_build_lines` (group view) and
  `_build_process_lines` (process view), right after the pulse row in both. Never touches
  `n_wk`/`n_id`/job counts (I8 — structurally separate function/line).
- `tools/fleet/fleet.py` — `_collect_governor()` + `--json` `governor` key (best-effort,
  omitted entirely when the source is absent — `memory` key precedent).
- `tools/fleet/tests/test_f28c_governor.py` (new, 6 tests) — real `state.json` shape fixture
  (`{"schema_version":1,"leases":{...},"starts":[]}`, matching the live shape observed during
  planning), dead-lease exclusion, missing-file/corrupt-json → `None`, mtime cache, env override.

### Healthy-quiet threshold — real observed basis, not guessed
Live `.runtime/model-worker-governor/state.json` (this repo, this cycle) shows **1 active lease
out of cap 5** (a single background `dispatch`-class lease) — 20%, comfortably under any
reasonable "worth a glance" bar. `_GOVERNOR_QUIET_FRACTION = 0.5` was picked so that single
steady-state lease stays silent (matches the F-12 "healthy board stays quiet" contract this
codebase already applies to the alert strip), while 3+/5 (60%) would surface. This is a judgment
call, not a hard requirement from the plan — recorded here per plan §6a's "구체 임계는 실측 후
dev_log에 근거 기록" instruction.

## 4b — resource-runner run registry (skipped, per plan's own pre-committed decision)
Not implemented. Full reasoning already recorded in `_internal/carryover.md` §2 (written during
Step 1, since the plan pre-committed this split before execute began — P2 in plan.md is not a
finding execute made, it is a finding the PLAN stage already made and instructed execute to
honor). Summary: `utilities/resource-runner.py --registry` is caller-supplied with no canonical
default, `dispatch-node.py` never asserts a fixed location, zero live files, zero
`resource-runner`-kind nodes in any real route record inspected — scanning a guessed path would
violate prd.md:292's "no guessing" rule outright. Re-open condition: a future stage-dispatch spec
revision that defines a canonical registry path (the way `.dispatch/jobs.log` or
`.runtime/model-worker-governor/state.json` already are).

## Test results
- `python3 -m unittest tools.fleet.tests.test_f28c_governor -v` → 6/6 OK.
- `python3 -m unittest discover -s tools/fleet/tests -t .` → **514 tests, 1 failure** (expected
  mirror-parity, deferred to Step 5). 508 (Step 3 total) + 6 new, **0 regressions**.
- G3 static read-only gate (`grep -nE "open\(.*['"]w|write_text|os\.replace|\.write\(" route.py
  collectors/governor.py`) → **0 lines output** — both new modules verified write-free.

## Known ambient-state note (not a bug, documented for Step 5 awareness)
`_governor_segs()` (unlike `_mem_summary_segs`, which receives its data as a caller-supplied
parameter) calls `collectors.governor.collect()` directly with no root override — it reads
whatever REAL `.runtime/model-worker-governor/state.json` this environment resolves to. This
matches the existing pattern `_build_lines`'s F-28a route-view resolution block already uses
(also a direct, unparameterized live read) and is a deliberate collector-self-resolves-its-env
convention already established in this codebase, not a new inconsistency introduced here. The
dedicated `test_f28c_governor.py` suite tests the collector itself hermetically via `root=`
overrides; `test_f30_process_view.py`'s render-level tests never assert on the governor row's
presence/absence (would be environment-dependent flakiness) — they only assert on route-card
content, which the governor row is orthogonal to.
