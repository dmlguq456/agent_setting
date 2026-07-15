# fleet v10 — scope carryover (execute stage findings)

## 1. Completion-gate PASS evidence (§3.3.1 B1) — decision: **honest gap, no carryover work item**

Probed during Step 1 (per plan §3.3.1's requirement): does any on-disk artifact mark a
completion gate as *passed* (as opposed to merely *declared* at launch)?

- `completion_gate=` in a jobs.log pipe row is written at **launch** time
  (`adapters/claude/bin/dispatch-headless.py:389` — `args.completion_gate` echoed verbatim into
  the pipe before the worker does any work). It is present on `status=open` rows for a node that
  has not even started.
- `utilities/capability-route.py`'s `complete` subcommand *would* write a
  `<evidence>.completion.json` marker (`:239`, `write_once`) — but a repo-wide search
  (`find ... -iname "*.completion.json"`) found **zero** such files anywhere under
  `/home/Uihyeop/agent_setting`. The `complete` subcommand exists in the tool but nothing in the
  current dispatch-headless/worker-route-guard pipeline invokes it.

**Decision (matches plan's pre-committed fallback)**: `route.py`'s node view carries
`gate` (the completion-gate *name*, from the record's `completion_gate` field) and no
`gate_passed`/pass-boolean key anywhere — not in `route.summary()`'s `--json` shape, not in the
F-30 card glyphs. This is a **structural absence of evidence**, not a bug: inventing a pass
signal from `completion_gate=` presence (or from `status=="done"` alone — prd.md:284's
`done,note=fleet-kill` marking proves `done` is not itself success) would be exactly the kind
of guessed indicator prd.md:292 forbids.

**Re-open condition**: if a future stage-dispatch spec revision makes `worker-route-guard.py`
(or an equivalent) write a real completion marker as part of node handoff, F-28/F-30 should pick
it up as a 5th glyph state or a dim `a`-detail annotation — the `route.py` node dict already has
room (`gate` field is separate from `state`), so this would be additive, not a rework.

## 2. detached resource-runner run registry (F-28c, prd.md:311) — decision: **skip, canonical
path does not exist**

- `utilities/resource-runner.py:18` takes `--registry` as a **required** CLI argument with no
  built-in default path.
- `utilities/dispatch-node.py:12` (the topology-registry side) only emits the runner *script*
  path for a `kind=="resource-runner"` node — it never asserts or documents a canonical registry
  file location.
- `.agent_reports/.runtime/` (this checkout, both real and every fixture-scale probe run during
  planning) has **zero** files that look like a resource-runner registry.
- Every real route record inspected during this cycle (`fleet-v10-process-view.route.json`,
  `agent-note-d1-route.json`, the v94-note-db-steward record) has **zero** `resource-runner`
  kind nodes.

Scanning a *guessed* path (e.g. `$ARTIFACT_ROOT/.runtime/resource-runner/registry.json`) would
violate prd.md:292's "no guessing" rule outright — there is no evidence such a path is even
meaningful, since the tool's own contract makes the registry path caller-supplied per-invocation
data, not a fixed resource.

**Distinction from "absent"**: prd.md:311 anticipated a binary "source absent → skip". The real
finding is narrower and more specific — the source (the `resource-runner.py` tool) is present
and real, but fleet (a passive external observer with no access to any dispatcher's specific
`--registry` argument) has **no discoverable path** to find its state. This is a
"**cannot be found**", not a "**does not exist**" — worth distinguishing for whoever picks this
back up.

**Resume condition**: if a future stage-dispatch spec revision defines a canonical
resource-runner registry location (the same way `.dispatch/jobs.log` is canonical for the job
registry, or `.runtime/model-worker-governor/state.json` is canonical for governor leases — see
`utilities/model-worker-governor.py:24-33 default_root()` for the shape such a canonicalization
would take), F-28c's resource-runner row can be implemented as a `collectors/resource_runner.py`
sibling of the new `collectors/governor.py` (Step 4a), following the exact same read-only +
mtime-cache + dead-lease-filter pattern.

model-worker-governor lease (the OTHER half of F-28c) was probed at the same time and judged
differently — real code **and** a real, canonically-resolvable live state file
(`.runtime/model-worker-governor/state.json`, `default_root()` gives a deterministic path) — see
Step 4a in `dev_logs/` for its implementation.
