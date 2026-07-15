# stage-dispatch v12 broker — Pipeline Summary

- Status: implementation and integrated verification complete; push/cleanup pending
- Spec: stage-dispatch PRD v12, SD-51~53
- Source branch: `stage-dispatch-v12-broker`
- Source worktree: `/home/Uihyeop/agent_setting-wt/stage-dispatch-v12-broker`
- Scope: harness-neutral depth-0 broker and Claude/Codex 4-placement compatibility
- Excluded: O2/O3 implementation

## Evidence

- v11 implementation gap confirmed: fallback helper executes target wrapper at caller locus.
- Official currentness confirmed: Claude native subagents cannot directly spawn subagents; Codex native depth and `codex exec` are separate surfaces. Portable recursion cannot be assumed.
- Source `8897bf76`, main integration `70bac6ef`.
- Four placement combinations PASS through one harness-neutral broker protocol.
- Broker protocol 10/10, portable guards 359/359, adaptation boundary/manifest/runtime projection PASS.

## Progress

- [x] v12 spec locked and pushed (`edb29709`).
- [x] implementation plan and plan-check.
- [x] implementation.
- [x] verification.
- [ ] push and guarded cleanup.

## Deferred spec judgment

- O2: propose `worker no-commit + prepared commit/evidence → depth-0 harvest/commit` for v13 evaluation; not implemented.
- O3: propose comparing evidence-bearing orchestrator override with compile-time digest pin + explicit drift record for v13; not implemented.
