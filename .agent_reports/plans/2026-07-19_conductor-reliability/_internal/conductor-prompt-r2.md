# Assignment — replacement autopilot-code conductor: conductor 신뢰성·Codex mutation·registry 위생

You are the replacement depth-1 `autopilot-code` owner for the immutable route
below. The first Codex owner and its Codex plan child were terminated by
depth-0 after a measured seven-minute no-progress condition: the child log
contained only `thread.started`/`turn.started`, emitted no analysis heartbeat
or artifact, and no host child process remained while launch heartbeat made
liveness report ALIVE. Depth-0 closed only those exact rows:

- owner `att-3c41dbecb6ec47f7a8f657357edf51b5`:
  `dead-parent-orphaned-manual-recovery`
- plan `att-f7e5cf8374024f069d844e0abb234ec0`:
  `dead-no-progress-namespace-child-vanished`

No completion marker or plan artifact exists. Resume at `plan`; do not treat
the failed attempt as completed.

Load `capabilities/autopilot-code.md` and `roles/worker-types/owner.md`
completely. Run separate registered `plan → execute → test → report` depth-2
workers and stay in this single `claude -p` turn until the final report exists.

## One-shot liveness contract

Never use Monitor, cron/wakeup scheduling, or end a turn to wait. After every
launch synchronously call:

```sh
sh /home/Uihyeop/agent_setting/utilities/dispatch-wait.sh --parent conductor-reliability-r2
```

Repeat immediately on exit 2. On no output/artifact/analysis heartbeat for two
120-second windows, diagnose as progress failure rather than treating the
launch heartbeat as sufficient. Use the checked cross-harness fallback only
after the exact failed row is terminal and the child is confirmed gone. One
active stage at a time.

## Immutable binding

- route:
  `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_conductor-reliability/_internal/route.json`
- route_id `rt-1d200b72bcfb544c`
- route_hash
  `sha256:1d200b72bcfb544c5d875d8c6b1a09f0bcef5a6741aaebeeeba60970b9c45c63`
- worktree:
  `/home/Uihyeop/agent_setting-wt/conductor-reliability`
- canonical plan root:
  `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_conductor-reliability/`
- governing spec:
  `/home/Uihyeop/agent_setting/.agent_reports/spec/stage-dispatch/prd.md`
  §13.7.6 SD-64 and §13.10 SD-69~71
- source commit `b93648241199d1901733e55c4e9755fa28b83779`
- scope, outcomes, verification floor, core-first ordering, and
  `selector-paths` exclusion are exactly those in
  `_internal/conductor-prompt.md`; read that packet fully. Do not edit
  `spec/**`, `utilities/dispatch-route.sh`, or its tests.

## Routing and dispatch

Before each launch run `usage-check.sh`. Use dispatch QA `thorough` and keep
pipeline intensity `strong` in each stage prompt.

- plan=`claude`, deep maker. This deliberate deviation avoids the pre-fix
  Codex primary `.spec-grounding` block and the measured nested Codex
  no-progress failure. It writes only durable plan/checklist artifacts.
- execute=`claude`, fast implementer. It owns source mutation and commits;
  core semantic changes must be committed before adapter/runtime changes.
- test=`codex`, deep reviewer, only after execute PASS. For this node, use the
  newly committed worktree `dispatch-node.py`/Codex wrapper so the
  `.spec-grounding` writable-root fix is self-hosted and directly tested. If
  the exact changed tool cannot safely self-host, use Claude and record the
  limitation instead of claiming Codex acceptance.
- report=`claude`, fast writer.

Start each node with the route-bound `dispatch-node.py`, absolute inputs and
outputs, parent `conductor-reliability-r2`, slug
`conductor-reliability-<stage>-r2`, `--qa thorough`, and its route model role.

After each stage:

1. harvest and exact-close only its current attempt;
2. write the completion marker;
3. verify the marker and exact row state;
4. only then start the next node.

For plan, use the current main `capability-route.py complete` after exact row
close. After execute implements SD-70, exercise the worktree
`capability-route.py complete --jobs ... --attempt-id ...` for test/report and
record any bootstrap boundary. Never breadth-close all route/node rows.

## Completion

Write the locked `pipeline_summary.md` and `final_report.md`, including both
failed first-owner attempts and the reason for the replacement. Do not merge
or push main. Finish exactly:

```text
artifact: /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_conductor-reliability/final_report.md
verdict: PASS | FAIL | BLOCKED
blocker: none | <one line>
```
