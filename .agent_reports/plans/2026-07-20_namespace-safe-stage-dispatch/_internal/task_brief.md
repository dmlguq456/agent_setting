# Namespace-safe stage dispatch — task brief

- Approval: user approved `autopilot-code · strong` on 2026-07-20.
- Primary outcome: preserve registered depth-2 stage sessions across Codex
  depth-1 tool-call PID namespaces without replacing cross-harness dispatch
  with Codex-native subagents.
- Worktree: `/home/Uihyeop/agent_setting-wt/namespace-safe-stage-dispatch`
- Canonical artifact root: `/home/Uihyeop/agent_setting/.agent_reports`
- Cycle: `plans/2026-07-20_namespace-safe-stage-dispatch`
- Existing blueprint:
  `.agent_reports/spec/stage-dispatch/prd.md`

## Confirmed user intent

The topology remains:

```text
depth-0 main -> depth-1 capability owner -> registered depth-2 headless stage
```

Depth-2 may be `codex exec`, `claude -p`, or another checked harness. Native
Codex subagents are fallback-only and must not become the primary path because
they cannot realize Codex-to-Claude stage dispatch.

## Observed failure

On 2026-07-20 the three Codex depth-2 attempts
`memory-oncall-promotion-plan{,-r2,-r3}` produced only 3, 4, and 2 JSONL lines.
They were launched from a Codex depth-1 tool call, recorded
`pid_scope=namespace-local`, and died when the tool call's transient PID
namespace ended. Commit `d04ee778` changed this silent death to typed
`nested-sandbox-lifetime` exit 77, but it did not make the stage complete.

Checked nested eligibility for this worktree is currently supported for both:

- Codex parent -> Codex child
- Codex parent -> Claude child

The remaining defect is launch lifetime, not auth, network, model selection,
or native-agent depth.

After this task worktree was created from clean commit `ff31c436`, the primary
checkout acquired uncommitted candidate edits to the Codex and Claude wrappers
that add an explicit `--foreground` switch. These edits belong to another
session or the user. Treat them as read-only candidate input:

```text
git -C /home/Uihyeop/agent_setting diff -- \
  adapters/codex/bin/dispatch-headless.py \
  adapters/claude/bin/dispatch-headless.py
```

Do not edit, reset, stage, or commit the primary checkout. Reproduce only the
validated intent in the task worktree and complete the missing automatic
`dispatch-chain` integration, lifecycle state, tests, and contracts.

## Required behavior

1. Keep the current detached launch behavior outside transient PID namespaces.
2. Inside a transient per-tool-call PID namespace, keep the wrapper/dispatch
   call alive until the selected child session reaches a terminal state.
3. Preserve exact global-registry attempt identity, Fleet visibility,
   progress heartbeat/watchdog, capacity failover, completion-marker binding,
   and ordered same-harness -> cross-harness -> native -> inline fallback.
4. Record the actual launch lifecycle (`detached` or a stable
   `foreground-scoped` vocabulary) in machine-readable wrapper output and the
   attempt row.
5. Do not edit `$CODEX_HOME/config.toml`, raise `agents.max_depth`, reintroduce
   the retired broker, or collapse depth-2 work inline except through the
   checked fallback and the self-modification exception below.
6. Update portable core first, then adapter realizations. Update the
   stage-dispatch PRD through an `autopilot-spec` transaction before claiming
   the new contract complete.

## Self-hosting constraint

This task modifies the dispatch mechanism required by its own `strong` graph.
The current depth-1 -> depth-2 background launch is the defect under repair.
Set and record:

```text
STAGE_DISPATCH_INLINE_OK=dispatch-infra-self-modification
```

Attempt the checked dispatch path only when it can fail fast without spawning a
doomed model session. If the existing exit-77 guard proves the runtime
unavailable, record the exact failure in `_internal/metrics.md` and execute the
bounded stage inline in the depth-1 owner. Do not silently claim independent
stage execution.

## Completion evidence

- Deterministic unit/conformance tests for namespace detection, detached
  compatibility, foreground-scoped completion, exact row closure, and timeout
  or signal handling.
- Live Codex depth-1 -> Codex depth-2 completion with an artifact, typed handoff,
  exact completion marker, and terminal registry row.
- Live Codex depth-1 -> Claude depth-2 completion with the same evidence.
- Existing dispatch, route, liveness, Fleet, projection, and boundary checks
  remain green.
- Source diff, verification commands, risks, and any unsupported parity surface
  are recorded in the cycle artifacts.
