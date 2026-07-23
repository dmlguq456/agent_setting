# Execution topology metrics

- capability: autopilot-code (primary), autopilot-spec update (secondary)
- mode: debug
- intensity: strong
- requested assurance: cross-harness 2-way independent verification
- current execution exception: self-hosting seam under repair
- evidence: without the depth-1 owner network marker both tuples correctly
  failed `nested-network-unconfirmed`; with the checked owner marker,
  Codex→Codex and Codex→Claude both returned `supported`. Strict Codex
  projection for the feature worktree remains inactive because the installed
  projection is correctly bound to the primary checkout.
- consequence: portable contract and lifecycle implementation are performed in
  the isolated worktree by depth-0, then Codex and Claude registered-headless
  verification is run against the integrated implementation. No depth-2 row is
  fabricated without a live registered parent.
- realized verification: Claude Code 2.1.218 and Codex CLI 0.145.0 were each
  invoked through their real stdin headless command. Their final `result` and
  `turn.completed` envelopes normalized to the same exact three-line PASS
  handoff. A separate registered Claude Code review produced a terminal
  artifact; its five must-fix items were incorporated into the contract.
- depth exception result: no synthetic owner or orphan row was introduced to
  test the lifecycle code while that lifecycle code was under repair. The
  exception is limited to implementation ownership; cross-harness behavior was
  still exercised through the real wrappers, terminal parser, liveness, and
  harvest paths.
- user-context policy: raw worker logs stay in artifacts; only typed verdicts
  and paths are returned to the parent.
