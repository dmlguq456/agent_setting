# Main/worker bootstrap boundary

- Date: 2026-07-15
- Mode: audit + dev
- Intensity: strong
- Primary capability: autopilot-code
- Spec significance: SPEC-SIGNIFICANT — D-42 changes portable lifecycle ownership and all adapter bootstraps.

## Goal

Make recursive model spawning structurally impossible from dispatch, loop, title,
distill, and native worker sessions while preserving deterministic safety and
task routing. Automatic memory and curator lifecycle remains owned by the
interactive main session only.

## Contract

1. `AGENT_SESSION_ROLE=worker` is the portable launch marker; legacy adapter
   markers also force worker behavior.
2. Workers perform no automatic memory injection, briefing, turn-nudge,
   SessionEnd sync/curation, title summarization, token-budget context, or
   interactive-pane publication.
3. Workers retain write/core/spec/artifact/worktree/permission guards,
   capability/mode/QA routing, explicit status signals, handoff, liveness, and
   verification.
4. All repo-owned model launchers set the marker before process creation.
5. Hook/preflight defenses no-op before state mutation or model invocation.
6. Verification is hermetic and launches no live model.

## Implementation

1. Add D-42 to the memory PRD and core memory/hooks/operations contracts.
2. Mark Claude, Codex, and OpenCode dispatches, loop runners, title refreshers,
   and distill workers as workers.
3. Split adapter lifecycle bridges into main-only context/model work and
   worker-retained deterministic safety/task work.
4. Add defense-in-depth worker gates to portable and adapter distill paths.
5. Add regression coverage, validate projections and physical hook parity, then
   activate the runtime projection without touching credentials or sessions.

## Plan check

- Can a stale wrapper omit the new marker? Compatibility markers still no-op.
- Can a main marker override a worker marker? No; any worker evidence wins.
- Are safety hooks disabled? No; only main-only lifecycle/context/model work is.
- Can worker exit mutate counters/stamps before returning? No; gates precede state.
- Does verification spend tokens? No; model boundaries use stubs/static checks.
