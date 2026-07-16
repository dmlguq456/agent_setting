# Direct Headless Resilience — completed plan

status: complete
capability: `autopilot-code`
scope: stage-dispatch v14 §13.6.2–13.6.4, retained by v15 §13.7.4
order: `SD-58 -> SD-59 -> SD-60`
implementation: direct headless only; broker lifecycle remains retired

## Invariants

- One shared F-25 exact-attempt classifier owns PID/start, attempt, route/node,
  heartbeat, and deterministic progress evidence.
- SD-58 state is bounded per attempt and synchronously observed; no daemon,
  resident watcher, socket, spool, lease, or supervisor is introduced.
- Wrappers detect and record capacity death; only the conductor chooses one
  validated alternative model and owns retry identity/cooldown.
- Registry reconciliation filters selected current work first, revalidates
  under the canonical lock, and preserves unsafe or unrelated rows.
- The retained `fleet-depth2-retry-liveness` work is F-25 attempt identity and
  newest-attempt presentation only. Broker recovery is withdrawn.

## SD-58 — progress watchdog

- Reuse `tools.fleet.model.classify_attempt_evidence` across Fleet, watchdog,
  liveness, and reconciliation.
- Emit exact launch/analysis/tool/file-write/test/artifact/terminal heartbeat
  phases from direct wrappers and generated stage prompts.
- Warn on the first unchanged deterministic window; after a second consecutive
  quiet window, revalidate exact PID/start, interrupt only that attempt, close
  it `dead-no-progress`, and resume the checked fallback chain.
- Require native child identity/artifact proof; capability support alone never
  proves that a child exists.

## SD-59 — capacity failover

- Anchor capacity classification to terse terminal CLI output in Claude,
  Codex, and OpenCode wrappers and close only the exact attempt
  `done,note=dead-capacity`.
- Keep replacement selection out of wrappers. Resolve adapter-paired settings
  from checked model maps, reject same/cooled/disallowed models, and perform at
  most one stable model-bound retry per route node.
- Preserve prompt, route/node, worktree, write scope, completion gate, and
  artifact ownership across that retry; descend the normal fallback chain if
  selection or retry fails.

## SD-60 — current view and reconciliation

- Provide current filters for session, route/node, attempt, and job before
  totals or decisions; default to the newest attempt per logical node.
- Classify active, exact-dead, safely merged, proven stale-terminal,
  namespace-local terminal, and unsafe rows using the shared classifier and
  SD-29 worktree safety evaluation.
- Keep dry-run as the default. On apply, re-read and reclassify under the
  canonical jobs lock, mutate the exact row atomically, and emit bounded audit
  evidence.

## Integration result

- Implemented across portable utilities, all three direct wrappers, Codex and
  OpenCode liveness projections, Codex preflight, worker prompts, Fleet, and the
  byte-identical Claude Fleet mirror.
- A real Codex root -> depth-1 headless owner -> depth-2 headless stage smoke
  completed through `same-harness-headless`, with `broker_lifecycle=retired`.
- That smoke exposed namespace-local child PID visibility. The final hardening
  marks such rows `pid_scope=namespace-local` and uses only an exact fresh
  heartbeat at root; terminal heartbeat becomes `done`, while stale/mismatched
  evidence falls back without probing an unrelated host PID.
- Focused, full Fleet, mirror, portable guard, adaptation-boundary, and runtime
  projection checks passed. Source and artifacts were merged/pushed on `main`.
  The direct-headless and broker-retirement worktrees were eligible and removed;
  the dirty predecessor Fleet worktree was deliberately preserved.
