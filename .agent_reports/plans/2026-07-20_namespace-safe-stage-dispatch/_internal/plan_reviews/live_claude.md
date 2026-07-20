# Live lifecycle smoke — Claude foreground-scoped transport

Bounded post-implementation live transport smoke for the `code-plan` node. This
is a review-only artifact; no source, plan, checklist, route, or PRD was
touched.

## Route / node / attempt identity (from environment + registry)

- capability: `autopilot-code`, mode `dev/refactor`, intensity `strong`, qa `standard`, depth 2, worker_type `stage`, worker_role/assigned_contract `code-plan`.
- owner `autopilot-code`, owner_harness `codex`, parent `namespace-safe-stage-dispatch-owner`, parent_session_id `019f7d9e-2e96-7371-88b4-2b9e6b272cee`.
- route_id `rt-0734fbe82e718115`, route_node `plan`, attempt_id `att-liveclaude0000000000000000000000000000000000000001`.
- worktree `/home/Uihyeop/agent_setting-wt/namespace-safe-stage-dispatch`; artifact_root `/home/Uihyeop/agent_setting/.agent_reports`; profile `-`.

## Did the Claude foreground-scoped wrapper lifetime reach this worker? — YES

Canonical registry `/home/Uihyeop/agent_setting/.dispatch/jobs.log` line 581 is
this exact worker's row and records the decisive fields:

```
slug=namespace-safe-live-claude  status=open  child_harness=claude  parent_harness=codex  depth=2
attempt_id=att-liveclaude0000000000000000000000000000000000000001  route_id=rt-0734fbe82e718115  route_node=plan
launch_authority=conductor  fallback_ordinal=2  eligibility_source=post-fix-live-foreground
pid=20  pid_start=803463  launch_lifecycle=foreground-scoped  pid_scope=namespace-local
```

- `launch_lifecycle=foreground-scoped` + `pid_scope=namespace-local` + `pid=20`
  (a namespace-local low PID) confirm the wrapper detected the transient nested
  PID namespace and selected the foreground-scoped path, then supervised a live
  child that is executing right now (row still `open`; the launcher waits in
  `wait_foreground` and closes the row on my terminal exit).
- Before/after evidence on the same route/node:
  - Pre-fix probe rows (lines 572 codex / 573 claude) both closed
    `note=dead-nested-sandbox-lifetime` — the detached path's exit-77 fail-fast
    fired and spawned no durable child.
  - Post-fix rows (line 580 `namespace-safe-live-codex`, line 581 this worker)
    carry `launch_lifecycle=foreground-scoped` and produced live children — the
    codex sibling reached the worker then `dead-worker-blocked`; this Claude
    worker reached execution and is producing this artifact.

Conclusion: the namespace-safe foreground-scoped dispatch is what allowed a live
depth-2 Claude `code-plan` worker to exist under a Codex owner inside a nested
PID namespace, where the prior detached launch was correctly fail-fast blocked.

## Implementation vs. approved plan — matches

Verified by reading the current worktree source against `plan.md` steps:

- Step 1 (preserve detached fail-fast): `adapters/claude/bin/dispatch-headless.py`
  lines 964–980 still fail-fast (`nested-sandbox-lifetime`, exit 77) for a
  DETACHED launch inside a PID namespace without the explicit override; the
  pre-fix registry rows 572/573 show it exercised.
- Step 3 (shared selector projected into wrappers): new
  `utilities/dispatch_lifecycle.py` provides `pid_namespace_scoped()` and
  `select_launch_lifecycle()`; `utilities/stage-dispatch-fallback.py` sets
  `args.launch_lifecycle = select_launch_lifecycle()` (main) and projects it via
  `--launch-lifecycle` (+`--foreground-timeout`) in `wrapper_command`.
- Step 4 (wrapper foreground-scoped support): Claude wrapper adds
  `--launch-lifecycle`/`--foreground-timeout`, calls `wait_foreground` (SIGINT/
  SIGTERM forwarding to the child group + timeout→SIGTERM→SIGKILL escalation,
  typed `ForegroundResult`), writes `launch_lifecycle=` into the attempt row
  (line 999), emits machine-readable `launch_lifecycle`/`worker_exit`/
  `worker_failure`, and closes the row on terminal failure.
- Step 2 (core semantics): `core/OPERATIONS.md` is modified consistent with the
  dispatch-chain lifecycle rule; the wrapper/selector code realization is
  self-consistent. (Core prose read only at the code-realization level here.)
- Step 5 (deterministic tests): `utilities/dispatch_lifecycle.test.py` and the
  adapter mirror `adapters/claude/utilities/dispatch_lifecycle.{py,test.py}`
  exist. Not executed in this worker — see Bash limitation below.

## Changed-file observations (git status snapshot)

- Modified: `adapters/claude/ADAPTATION.md`, `adapters/claude/bin/dispatch-headless.py`,
  `adapters/codex/ADAPTATION.md`, `adapters/codex/bin/dispatch-headless.py`,
  `core/OPERATIONS.md`, `tools/check-adaptation-boundary.sh`,
  `utilities/dispatch_adapters_v11.test.py`, `utilities/stage-dispatch-fallback.py`,
  `utilities/stage_dispatch_fallback.test.py`.
- New (untracked): `utilities/dispatch_lifecycle.py`, `utilities/dispatch_lifecycle.test.py`,
  `adapters/claude/utilities/dispatch_lifecycle.py`, `adapters/claude/utilities/dispatch_lifecycle.test.py`.
- checklist.md still marks steps 5–15 unchecked, but source + tests are already
  in place, i.e. implementation has progressed ahead of the checklist marks.

## Commands actually run

- `dispatch-progress.py heartbeat … --phase analysis` (SD-58 entry) — **FAILED**.
  Every `Bash` tool call in this worker fails with
  `EROFS: read-only file system, mkdir '/home/Uihyeop/.claude/session-env/<uuid>'`,
  a harness pre-exec step, regardless of sandbox toggle. No shell command could
  execute, so the SD-58 heartbeat contract could not be honored from inside this
  foreground-scoped worker.
- `Read` (source, plan, checklist, jobs.log) — succeeded; used for all evidence
  above. Progress here is evidenced by the durable artifact write and the live
  registry row rather than by heartbeats.

## Limitation / caveat

The foreground-scoped transport delivered a live, executing Claude worker
(transport goal met), but this worker's `Bash` surface is unavailable
(session-env root mounted read-only). That is orthogonal to the launch-lifecycle
change — it does not regress the fix — but it means a foreground-scoped Claude
child in this sandbox cannot emit its own heartbeats or run tests; Fleet
progress for such a child must rely on the parent wrapper's seed launch
heartbeat, not child-emitted SD-58 beats. Recommend recording this as a known
environment constraint of the live drill.

## Verdict

PASS — the approved plan is implemented and the Claude foreground-scoped wrapper
lifetime demonstrably reached this live depth-2 worker (registry line 581,
`launch_lifecycle=foreground-scoped`), with the Bash/heartbeat unavailability
recorded as an environment caveat rather than a lifecycle defect.
