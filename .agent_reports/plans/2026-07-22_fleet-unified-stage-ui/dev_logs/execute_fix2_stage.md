# code-execute fix2 stage artifact

- route: `rt-dfec3aabe921b37f`, node `execute`, attempt `att-aae6de402638cfed0535adb06d383b1af8eb8d37ab0612a2`
- capability/mode/QA: `autopilot-code` / `dev/refactor` / standard code
- write scope honored: canonical `tools/fleet/**`, plan checklist, and execute log; no commit/push/merge/cleanup
- assurance: `plan-check:selected-independent-pass:final-verify`

## Changed source and tests

Canonical changes were made under:

```text
tools/fleet/projection.py
tools/fleet/model.py
tools/fleet/render.py
tools/fleet/demo.py
tools/fleet/tests/test_f36_work_projection.py
tools/fleet/tests/test_f37_context_detail.py
tools/fleet/tests/test_dispatch.py
tools/fleet/tests/test_f15_rows.py
```

The pre-existing v16 source/test diff also covered the collector, fleet, route,
title, fixture, and related Fleet test paths. After canonical gates passed, the
complete tree was mirrored with the prescribed rsync; `diff -rq` and the mirror
parity test pass. Total task-tree inventory at handoff: 60 paths (48 tracked,
12 new), canonical and mirror relative paths identical.

## Implemented corrections

1. Unique exact `(pid,proc_start)` route candidates are adopted; only when exact
   identity evidence is absent is one same-harness realpath-cwd candidate used.
   PID reuse and duplicate cwd candidates fail closed.
2. `attempt_id` alone is not a route tuple. Session and dispatch owners traverse
   `session_id/parent_sid` or `slug/parent_slug`; same-route siblings remain
   visible and direct owner/child disagreement returns `owner-route-conflict`.
3. Group rendering consumes each attached WorkProjection. Render-local first
   child/first route overrides were removed; ambiguous/explicit-invalid rows do
   not revive fixed pipeline stages.
4. Main Session rows show attached stage/progress at 168/120/100/60 and the
   process view interleaves job -> context/NOW -> exact-session sub-agent strip.
5. Sealed DAG record order and opaque sibling/fan-in metadata remain intact.
   Route JSON preserves legacy node `model`, `harness`, `effort`, `elapsed_min`,
   and `note` meanings while adding v16 data; private evidence remains absent,
   and public ambiguity serializes as an array.
6. Demo route linkage is deterministic and provider-disabled.

## Verification evidence

| Check | Result |
|---|---|
| Focused correction regressions | 37/37 PASS |
| Codex verification-runner Fleet discovery | 773/773 PASS |
| `utilities/compose_route.test.py` | 9/9 PASS |
| `utilities/capability_route.test.py` | 30/30 PASS |
| sealed composed fixture capability-route verify | PASS (`rt-63788ad671654b75`) |
| provider-disabled group/process once and public JSON parse | PASS |
| canonical+mirror compileall | PASS |
| mirror parity, `diff -rq`, `git diff --check` | PASS |
| adaptation guard | PASS; all negative sentinel tests |
| adaptation boundary | PASS exit 0; 127 documented adapter-mapping warnings |

## Warnings / unsupported runtime details

- PRD read completed, but the preflight read marker could not be written:
  `.spec-grounding` is read-only in this worker environment.
- Collector sequence/head is bounded to the observed same-sample source
  contract; resolver freshness/regression refusal is hermetically tested without
  claiming unavailable production evidence.
- Independent selected review is owner-controlled and is not claimed by this
  depth-2 worker; the previous review’s two red findings were corrected and all
  execute gates are green.

## Correction-cycle wording and boundary

The OpenCode refresher uses only an ephemeral, consistency-checked private
snapshot of the source database plus an already-existing WAL. It never copies
or opens the source SHM, never persists the snapshot, and never writes the
source DB/WAL/SHM. Persistent database copies remain forbidden; the private
snapshot is the explicitly allowed read boundary for a live WAL.

## Correction-cycle verification handoff

- Canonical source/test scope: `tools/fleet/**`, `utilities/model-worker-governor.py`, and v16 Fleet tests; the Claude mirror was synchronized only afterward with the prescribed rsync.
- Owner aggregation: `resolve_work_projection` derives owner labels from every active sealed node in record order. Focused F-36/F-28b/F-30 regressions cover reversed input and all required widths.
- Composed fixture/demo: route, breadcrumb, process-card, populated old-key JSON, and deterministic provider-disabled demo coverage added. Exact group primary row: `stage {claim-a,claim-b} 1/4`; process card: `rt-63788ad6 — 1/4 nodes` with `claim-a` and `claim-b`.
- F-39: test governor root is isolated under its temp directory with governor env restoration; central title class ceiling is 4 and parity-tested; live WAL snapshot regression passes with source DB/WAL/SHM/journal signatures and bytes unchanged.
- Verification: Fleet `781/781`; compose `9/9`; capability route `30/30`; sealed fixture verify PASS; provider-disabled group/process/JSON PASS; compileall PASS; canonical/mirror diff and parity PASS; `git diff --check` PASS; adaptation guard PASS.
- Adaptation boundary: FAIL, with three repository-existing blockers: missing valid baseline hashes for `adapters/claude/hooks/mem-distill-dispatch.sh` and `adapters/claude/utilities/agent-worklog-state.sh`, plus `adapters/claude/CLAUDE.md` at 16385 bytes over the 16384-byte ceiling. One documented concrete-reference warning remains.
- No provider was invoked by verification; no commit, push, merge, cleanup, or completion marker was performed.
