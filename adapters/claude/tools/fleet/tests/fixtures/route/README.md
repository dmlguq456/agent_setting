# route/ fixtures (F-28a, plan §3.5)

- `real_claude_staged.json` — verbatim copy of the real record compiled for THIS execute cycle
  (`/home/Uihyeop/agent_setting/.dispatch/logs/fleet-v10-process-view.route.json`), route_id
  `rt-27f7bc9ff152ba13`.
- `real_codex_staged.json` — verbatim copy of a real codex-runtime record
  (`/tmp/agent-note-d1-route.json`, since evicted — /tmp volatility is the point of the
  fixture), route_id `rt-1120bb39a13c4191`.
- `synth_broken_hash.json` — `real_claude_staged.json` with `capability` mutated by one
  character (`autopilot-code` → `autopilot-codf`), `route_hash`/`route_id` left untouched (now
  stale) — exercises `load()`'s hash-recheck rejection (T1-5).
- `synth_bad_schema.json` — `real_claude_staged.json` with `schema_version: 2`; `route_hash`/
  `route_id` were RECOMPUTED (via `route.route_hash()`) so the row is internally consistent —
  the only thing that must reject it is the schema-version guard (T1-6).
- `synth_parallel_lab.json` — synthetic (no real counterpart): `autopilot-lab/eval` topology,
  `setup → {eval-asr, eval-sep, eval-vad} → aggregate → report` (3-way fan-out + fan-in).
  `route_hash`/`route_id` generated with `route.route_hash()` (see the one-off script below) —
  never hand-write a hash, `load()` rejects it immediately.
- `jobs_route.log` — 4 real jobs.log rows (verbatim field values, tab-separated, per the
  writer's own vocabulary), with `route_file=` for two of them rewritten to the `{FIXDIR}`
  placeholder (tests `.format(FIXDIR=<tmpdir>)` before use, then drop this fixture dir's own
  copies of `real_claude_staged.json`/`real_codex_staged.json` alongside it) — the other two
  keep their real (now-gone) `/tmp` paths verbatim, proving the tolerant-fallback path.

Regeneration one-liner for the synth files (route_hash/route_id must always come from the
function, never hand-written):

```python
import json, sys; sys.path.insert(0, "tools")
from fleet import route as routemod
payload = {...}  # schema_version 1 dict, no route_hash/route_id yet
digest = routemod.route_hash(payload)
payload["route_hash"] = digest
payload["route_id"] = "rt-" + digest.split(":", 1)[1][:16]
```
