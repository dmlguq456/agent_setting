# Runtime activation Phase 1 dispatch metrics

## Separability and fallback

- The depth-1 capability owner started normally and attempted the required
  depth-2 `code-plan` stage twice.
- Attempt 1 failed before model startup because the generated read-only Codex
  home could not initialize the in-process app-server client.
- Attempt 2 used an isolated runtime projection but read-only sandbox networking
  blocked the model request. Both failed rows were harvested.
- The owner then announced a native subagent but emitted only empty-recipient
  wait calls; no worker id or artifact existed after repeated polls. The stuck
  owner was terminated and harvested.
- Runtime activation changes the common CLI, transaction engine, three runtime
  projections, state schema, and one coupled E2E contract. With dispatch
  infrastructure itself unable to produce a stage artifact, execution proceeds
  inline under the documented fallback. Read-only census/test/OpenCode analysis
  was still delegated independently; implementation remains single-writer.
