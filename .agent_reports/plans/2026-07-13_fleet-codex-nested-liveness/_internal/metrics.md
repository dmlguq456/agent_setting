# Metrics

- intensity: standard
- qa: standard
- stage_execution: inline
- `STAGE_DISPATCH_INLINE_OK=1`
- separability: dispatch/Fleet infrastructure self-modification; spawning another worker through the liveness path under repair would not provide an independent execution boundary. Work is isolated in a dedicated git worktree and independently exercised by hermetic tests plus the live registry fixture.
