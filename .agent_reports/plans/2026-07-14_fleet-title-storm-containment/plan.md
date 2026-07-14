# Fleet title storm containment

## Objective

Prevent automatic title and memory-distill model workers from recursively or cumulatively exhausting tokens, CPU, or memory across many session IDs.

## Plan

1. Keep live provider paths disabled and terminate only workers carrying the explicit title-refresh marker.
2. Cut internal-session recursion at Fleet scheduling and make every title-provider ingress share global concurrency, rolling-start, stale-recovery, and kill-switch guards.
3. Replace the distill dispatcher's racy count guard with atomic fixed slots plus a persistent rolling start budget; synchronize the Claude runtime copy.
4. Verify with provider-free 200-session Python fixtures and sleeping shell stubs, then run Fleet, memory-dispatch, mirror, and adapter-boundary regressions.
5. Leave destructive transcript cleanup and distill re-enablement outside this cycle.

## Acceptance

- Title backlog: at most 2 concurrent starts and 4 starts per rolling 600 seconds by default.
- Distill backlog: at most 2 concurrent starts and 4 starts per rolling 10 minutes by default.
- Internal/memory/child/app-server sessions never become title targets.
- Runtime kill switches cause zero model-provider starts.
- No live provider is invoked during verification.
