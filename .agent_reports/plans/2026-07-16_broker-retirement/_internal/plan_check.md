# Plan Check

Verdict: PASS

- Scope replaces broker responsibilities instead of merely deleting files.
- Canonical registry, model governor, completion markers, and worktree isolation remain.
- Direct nested Codex requires an explicit parent execution boundary; child flags cannot escalate it.
- Stable attempt claim covers the idempotency responsibility previously hidden in broker request state.
- v1/v2 are migration-only and cannot be newly compiled.
- No spool, watcher, supervisor, or renamed broker is allowed.

Independent reviewer addendum: require direct failure fallback, concurrent duplicate coverage, v1/v2 read compatibility, Fleet exact identity, and a negative assertion that no resident broker/watcher remains.
