# Implementation log

## Root cause

Codex depth-1 dispatch callers could pass a synthetic `--parent-session-id`,
which took precedence over the parser's `CODEX_THREAD_ID` default. Fleet could
recover from a stale id by matching `parent_cwd` only while that cwd identified
one visible session. With multiple Codex/Claude sessions in the same repository,
the cwd is intentionally ambiguous and the owner was rendered as `(orphan)`.

## Change

- Bind depth-1 Codex dispatch metadata to the current `CODEX_THREAD_ID` (or
  `CODEX_SESSION_ID`) and clear a synthetic logical parent slug.
- Preserve explicit depth-2 owner/broker parent metadata unless the existing
  checked force switch is set.
- Keep Fleet's ambiguous-cwd fail-closed behavior unchanged and add canonical
  plus Claude-mirror renderer coverage.

No native fallback, broker lifecycle, worker waiting, or liveness behavior was
changed.
