# Fleet v16 code-execute correction stage log

## Route, scope, and assurance

- Route: `rt-dfec3aabe921b37f`, node `execute`, current attempt `att-82d1553e89a447b193bc24a361d48c9a`.
- Capability/mode/QA: `autopilot-code` / `dev/refactor` / standard code.
- Required assurance: `plan-check:selected-independent-pass:final-verify` (preflight QA policy PASS).
- No commit, push, merge, cleanup, provider call, asynchronous wait, or live harness state write.
- Project-level `AGENTS.md` is absent in the worktree; the supplied project/kernel instructions and the Codex code-execute/native mode contracts were used.
- Spec-backed read: Fleet PRD `/home/Uihyeop/agent_setting/.agent_reports/spec/agent-fleet-dashboard/prd.md` and mode `[cli]` read successfully. The owner-side `.spec-grounding` read marker remains unavailable/read-only as recorded by the approved plan.

## First attempt and fallback evidence

- First Codex attempt implemented the main v16 seams but failed the canonical 744-test run with 19 failures and 2 errors.
- The supported cross-harness fallback migrated direct-construction/title/route assertions, then terminated without transcript, artifact, mirror, or completion marker.
- This correction audited the partial worktree diff. The initial focused state had 203 tests with 3 failures and 4 errors; the canonical state then had 7 failures, all process-view/mirror drift. Root cause was terminal node evidence not accepted by projection attachment and direct render paths not consuming that evidence.

## Implementation completed

- Added additive `ContextProjection`, private `ContextEvidence`, `ActiveNodeProjection`, `ProgressProjection`, and fail-closed `WorkProjection` serialization.
- Added common projection resolution with validated-route, registry, owner/conductor, exact artifact cardinality, ambiguity, and terminal node evidence handling.
- Added arbitrary opaque composed-DAG/fork/fan-in preservation, same-route sibling retention, route `write_scope`, route diagnostics, and JSON-safe route summaries.
- Added exact `(harness,pid,proc_start)` child association with atomic title/NOW/context adoption, PID reuse/cwd ambiguity/cross-harness refusal, and parent-context non-inheritance.
- Routed group/process/plain/JSON surfaces through attached projections and one context-first subordinate row; removed renderer PID-only joins and independent stage authority.
- Added exact QA-only artifact resolution and per-harness Claude/Codex `(mtime_ns,size)` context evidence alongside OpenCode `(time_updated,rowid)` evidence.
- Retained title scheduler bounds at concurrency `3`/hard `4`, rolling `4`/`60s`, main/child debounce `600`/`150`, direct-worker leases, no-tools/default shell-free behavior, and typed OpenCode read-only cursor plumbing.
- Added focused acceptance tests `test_f36_work_projection.py`, `test_f37_context_detail.py`, `test_f38_context_orthogonality.py`, `test_f39_title_quota.py` and sealed `synth_composed_survey.json` fixture.

## Exact canonical changed files

```text
tools/fleet/collectors/__init__.py
tools/fleet/collectors/claude.py
tools/fleet/collectors/codex.py
tools/fleet/collectors/dispatch.py
tools/fleet/collectors/opencode.py
tools/fleet/collectors/procscan.py
tools/fleet/fleet.py
tools/fleet/model.py
tools/fleet/projection.py
tools/fleet/refresh_title.py
tools/fleet/render.py
tools/fleet/route.py
tools/fleet/titles.py
tools/fleet/tests/fixtures/route/README.md
tools/fleet/tests/fixtures/route/synth_composed_survey.json
tools/fleet/tests/test_dispatch.py
tools/fleet/tests/test_dispatch_child_titles.py
tools/fleet/tests/test_f15_rows.py
tools/fleet/tests/test_f16_f17_subtitle.py
tools/fleet/tests/test_f17_title_refresh.py
tools/fleet/tests/test_f28_breadcrumb.py
tools/fleet/tests/test_f28_route.py
tools/fleet/tests/test_f30_gate_passed.py
tools/fleet/tests/test_f30_process_view.py
tools/fleet/tests/test_f36_work_projection.py
tools/fleet/tests/test_f37_context_detail.py
tools/fleet/tests/test_f38_context_orthogonality.py
tools/fleet/tests/test_f39_title_quota.py
tools/fleet/tests/test_wide_ctx_gauge.py
```

Exact mirror files are the same relative paths under `adapters/claude/tools/fleet/`, synchronized with the prescribed `rsync -a --delete --exclude='__pycache__' tools/fleet/ adapters/claude/tools/fleet/` operation. No hook or baseline file was intentionally changed.

## Verification commands and results

| Command | Result |
|---|---|
| `preflight.sh stage-heartbeat ... phase analysis` | PASS on entry; later heartbeat emission reported `progress-attempt-missing` after the registered attempt state changed externally |
| `preflight.sh qa-policy standard code` | PASS; `plan-check:selected-independent-pass:final-verify` |
| `worker-route-guard.py validate` / route recheck | PASS for immutable route scope before work |
| `preflight.sh read .../spec/agent-fleet-dashboard/prd.md codex-headless` | PRD read PASS; `.spec-grounding` marker degraded/read-only |
| Focused process/context/title/route tests | PASS; 130 initially after repair, then 155 changed-area tests, then focused v16 suites PASS |
| Focused acceptance tests | PASS; 17 tests, then 19 after QA-owner additions |
| Canonical Fleet tests excluding deferred mirror parity | PASS; 765 tests |
| Full canonical Fleet suite after final mirror | PASS; 766 tests |
| `utilities/compose_route.test.py` | PASS; 9 tests |
| `utilities/capability_route.test.py` | PASS; 30 tests |
| `capability-route.py verify --route tools/fleet/tests/fixtures/route/synth_composed_survey.json --cwd "$PWD"` | PASS; route `rt-63788ad671654b75`, sealed hash verified |
| Group/process `fleet.py --once` with `FLEET_DEMO=1 FLEET_TITLE_DISABLE=1 AGENT_DISPATCH_JOBS=/dev/null` | PASS; both views exit 0 |
| Public JSON plus `python3 -m json.tool` | PASS; additive old keys/context/work projection, private evidence absent |
| Canonical+mirror `compileall` | PASS |
| `test_mirror_parity` | PASS; 1 test |
| `bash tools/adaptation-guard.test.sh` | PASS (expected delta-baseline guard regression case) |
| `bash tools/check-adaptation-boundary.sh` | FAIL, pre-existing unrelated delta-baseline metadata: `adapters/claude/hooks/mem-distill-dispatch.sh` expected baseline `d07c732c...` but current hash is `aa342056...`; neither hook nor baseline file is changed in this attempt. |

## Warnings and gate status

- All Fleet, compose, compiler, mirror, compile, smoke, and no-provider acceptance gates pass.
- Full adaptation boundary remains blocked by the two unrelated pre-existing baseline records above. This worker did not run `build-manifest.py --sync-baselines`, because that would mutate out-of-scope adaptation metadata.
- The registered attempt is still represented as an open jobs row, but the progress heartbeat helper later rejected the attempt as `progress-attempt-missing`; no completion marker was emitted because the adaptation boundary gate is not complete.
- No live/default/custom title provider was invoked by tests or smoke; provider subprocess surfaces were fail-if-reached/monkeypatched in the hermetic suites.
- Compose/compiler behavior was verified through their canonical utilities; Fleet does not duplicate their compiler logic.
- Checklist was updated only for implemented and evidenced rows; adaptation-boundary and any unsupported/uncaptured acceptance rows remain unchecked.

## Finalizer revalidation

- Task-owned diff guard: PASS; no diff in `adapters/claude/CLAUDE.md`, `adapters/claude/hooks/mem-distill-dispatch.sh`, or adaptation baseline metadata.
- Focused F-36..F-39 tests: PASS; 20 tests.
- Canonical-to-Claude Fleet mirror parity: PASS; 1 test.
- Full Fleet suite: PASS; 766 tests.
- `python3 tools/build-manifest.py --check`: PASS; delta baselines bound.
- `bash tools/check-adaptation-boundary.sh`: PASS in the finalizer worktree. The previously recorded `adapters/claude/hooks/mem-distill-dispatch.sh` baseline warning (`d07c732c...` versus the prior observed `aa342056...`) remains unrelated to this task and is not treated as an execute failure.

Verdict: PASS; all task-owned execute gates pass, with the documented unrelated adaptation-boundary warning retained.
## 2026-07-22 — fresh corrective execute fix2 (`att-aae6de402638cfed0535adb06d383b1af8eb8d37ab0612a2`)

### Scope and source paths

- Canonical source ownership stayed under `tools/fleet/**`: `projection.py`,
  `model.py`, `render.py`, `demo.py`, the existing collector/fleet/route/title
  changes, route fixture README/fixture, and Fleet tests.
- The canonical correction added exact identity/cwd adoption, attempt-only
  parent-link traversal, direct owner/child conflict refusal, projection-only
  row stage rendering, process chunk ordering, sealed record-order rendering,
  additive old-key route JSON, and public `ambiguity[]` serialization.
- The deterministic demo now links the route conductor to the main demo
  Session; `--once`/`--json` remain provider-disabled.
- After canonical verification passed, the prescribed command synchronized the
  complete mirror: `rsync -a --delete --exclude='__pycache__' tools/fleet/
  adapters/claude/tools/fleet/`. Canonical and mirror are byte-identical.
- Git inventory at handoff: 60 task-tree paths (48 tracked modifications and 12
  new canonical/mirror files); no git metadata, commit, push, merge, or cleanup.

### Focused correction evidence

- `test_f36_work_projection.py`, `test_f37_context_detail.py`, legacy
  breadcrumb/folding migrations: 37/37 PASS in the focused run.
- Exact `(pid,proc_start)` adoption and unique same-harness realpath-cwd
  adoption PASS; PID-reuse and duplicate-cwd refusal PASS.
- Session `session_id/parent_sid`, DispatchJob `slug/parent_slug`, attempt-only
  owner traversal, same-route siblings, multiple routes/hashes, and direct
  owner/child `owner-route-conflict` PASS.
- Main Session stage/progress is visible at wide 168/120, narrow 100, and stack
  60; process chunks are job -> context/NOW -> exact-session sub-agent strip.
- Old route node keys `model`, `harness`, `effort`, `elapsed_min`, and `note`
  retain their attached backing-view meanings; private evidence is absent and
  public WorkProjection ambiguity is an array.

### Final gates and counts

| Command/evidence | Result |
|---|---|
| Codex verification-runner Fleet discovery | PASS, 773/773 |
| `utilities/compose_route.test.py` | PASS, 9/9 |
| `utilities/capability_route.test.py` | PASS, 30/30 |
| sealed `synth_composed_survey.json` capability-route verify | PASS, `rt-63788ad671654b75`, sealed hash verified |
| provider-disabled `--once --view group` | PASS; demo main Session visibly shows `stage execute 1/4` |
| provider-disabled `--once --view process` | PASS; route/degrade/context output rendered |
| provider-disabled `--json | json.tool` | PASS |
| canonical + mirror `compileall` | PASS |
| mirror parity and `diff -rq` | PASS |
| `git diff --check` | PASS |
| `bash tools/adaptation-guard.test.sh` | PASS; all negative sentinel tests |
| `bash tools/check-adaptation-boundary.sh` | PASS; documented warning only for 127 adapter mapping references |

### Warnings and runtime-contract limits

- `preflight.sh read .../prd.md` completed the PRD read but could not create
  the `.spec-grounding` marker because that filesystem is read-only.
- The full independent review gate is owner-controlled and is not claimed by
  this depth-2 worker; the prior review failure was corrected and the execute
  gates above are green.
- Collector sequence/head values are bounded to the observed same-sample
  source contract; resolver tests prove regression/freshness refusal, while no
  unavailable production telemetry is overclaimed.

Assurance: `plan-check:selected-independent-pass:final-verify`
