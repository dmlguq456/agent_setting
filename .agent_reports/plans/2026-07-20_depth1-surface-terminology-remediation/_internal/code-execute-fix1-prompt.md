# Code-execute bounded continuation 1

Resume route node `execute` in the existing dirty worktree. The first
same-harness attempt was blocked by linked-worktree git metadata; the
cross-harness attempt successfully applied approved commits `7094c92b` and
`c95ed391` and implemented only a partial compiler/topology layer. Read the
full durable state in `plan.md`, `checklist.md`, and
`dev_logs/execute-partial.md`. Preserve all valid existing changes and finish
the full code-execute completion gate; do not restart or discard work.

Complete every explicitly remaining item from `execute-partial.md`, including:

- wrapper/registry/fallback/liveness qualified `dispatch_depth` fields;
- closed `execution_surface`, boolean `registered_worker`, and `fallback_hop`
  validation before route/registry/spawn;
- real quick single-live registered-headless attempts, serial retry history,
  exact exhaustion/unavailable errors, and zero-emission prohibited cases;
- adapter wrapper CLI/metadata propagation across Claude, Codex, OpenCode;
- completion and Fleet model/collector/render/control/fixture propagation plus
  the generated Claude Fleet mirror;
- current canonical prose and four-surface terminology across core,
  capabilities, portable skills, runtime adapters and plugin projections;
- fresh direct/quick/standard+ route acceptance fixtures and deterministic
  negative/preservation tests;
- generator/sync propagation from canonical sources.

Do not touch retired broker-only bare-depth fields when they are explicitly
versioned/read-only legacy, and do not change Codex `agents.max_depth`. Do not
introduce rejected commit `6b3a34bc` or its composition contract. Run
preflight write before each edit, use repository generation/sync commands for
owned projections, update the checklist and write a new durable continuation
log under `dev_logs/`. Run enough focused checks to hand a coherent complete
diff to `code-test`. Do not commit. Return PASS only when the entire execute
gate is met; otherwise identify exact remaining work. End with the exact
three-line worker handoff.
