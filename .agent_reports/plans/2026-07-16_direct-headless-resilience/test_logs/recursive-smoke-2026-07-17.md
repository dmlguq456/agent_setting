# Recursive Codex headless post-fix smoke

verdict: **PASS**
date: 2026-07-17
source before diagnostic fix: `5972a61d`
diagnostic fix: `41093b61`

## Runtime topology

`root -> Codex depth-1 headless owner -> Codex depth-2 headless code-plan stage`

- Owner slug/attempt: `depth2-success-owner-20260717-0900` /
  `att-d091b0d18cdf47d7acf532358e6167a3`.
- Stage slug/attempt: `depth2-success-stage-20260717-0900` /
  `att-ac32010e484ef388dfedbaa676f3d65d7b729f725f2459a0`.
- Route/node: `rt-8d488ef332a0bb14` / `plan`.

The depth-1 owner ran with `workspace-write`, owner-only network access, and a
worktree-local `CODEX_HOME`. It directly started a separate depth-2
`codex exec`; the stage had no network access and used no native subagent or
broker path.

## Live and terminal evidence

While both processes were running, the selected registry contained exactly one
owner row and one stage row. The stage row recorded:

```text
depth=2
parent=depth2-success-owner-20260717-0900
attempt_id=att-ac32010e484ef388dfedbaa676f3d65d7b729f725f2459a0
launch_authority=conductor
fallback_ordinal=1
pid=437
pid_scope=namespace-local
```

Root liveness classified both rows `ALIVE`; the stage reason was
`namespace-local exact heartbeat`, so the host never probed the namespace-local
numeric PID as host identity. The stage emitted launch, analysis, tool, and
terminal heartbeats, ending at sequence 4 with evidence
`depth2-success-complete`.

The owner received:

```text
check=ok
selected_hop=same-harness-headless
launch_authority=conductor
broker_lifecycle=retired
attempt_trace=...:direct:exit-0:...|...:watchdog-terminal
```

Both Codex transcripts ended with `verdict: PASS`. Exact reconciliation closed
the namespace-local stage from its terminal heartbeat and left `open 0`.
There was no duplicate stage slug/attempt and no broker server process.

## Diagnostic defect found and fixed

An intentionally invalid portable role reproduced a real observability defect:
the Codex wrapper raised an unstructured traceback, and
`stage-dispatch-fallback.py` discarded it before reporting only
`runtime-unavailable`.

Commit `41093b61` now:

- converts role-map lookup errors to structured
  `reason=invalid-dispatch-model-role` with exit 64;
- preserves the last direct failure's attempt, exit, reason, and bounded detail
  when the chain reaches inline fallback;
- prevents the traceback from escaping; and
- adds an end-to-end regression test.

The resulting output contains:

```text
last_direct_failure_exit=64
last_direct_failure_reason=invalid-dispatch-model-role
last_direct_failure_detail=codex model-map: unknown role: not-a-role
```

## Verification

- `stage_dispatch_fallback.test.py`: 8 PASS.
- `stage_dispatch_capacity.test.py`: 6 PASS.
- `dispatch_adapters_v11.test.py`: 6 PASS.
- `worker_dispatch_prompt.test.py`: 2 PASS.
- `dispatch-headless.sd45.test.py`: 1 PASS.
- Codex SD-15 shell conformance: PASS.
- Python compile and `git diff --check`: PASS.

A full portable-guards diagnostic run completed at `357 PASS / 11 FAIL`.
Those failures were existing broad dispatch/harvest/runtime-projection fixture
assertions across Codex, Claude, and OpenCode; none touched the changed files or
the new diagnostic test. The focused contracts above are the acceptance
evidence for this patch.

## Controlled negative observations

- A 20-second deliberate quiet interval under a 10-second progress window
  correctly triggered `dead-no-progress`; this confirms SD-58 rather than a
  recursion failure.
- Reusing that failed route/node correctly skipped an unchanged tuple through
  the immutable prior-failure guard. The final passing smoke therefore used a
  freshly probed route and registry.
