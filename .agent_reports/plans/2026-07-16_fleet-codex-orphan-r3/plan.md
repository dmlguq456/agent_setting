# Fleet Codex parent attribution hotfix

- mode: `debug`
- intensity: `standard`
- spec-significance: `within-spec`
- scope: Codex depth-1 parent identity and Fleet regression coverage only

## Plan

1. Bind a Codex depth-1 dispatch to the actual current `CODEX_THREAD_ID`, even when a caller supplies a synthetic `--parent-session-id`.
2. Preserve explicit logical parent identity for depth-2 broker launches and retain Fleet's fail-closed ambiguous-cwd behavior.
3. Add wrapper and renderer regressions for synthetic-ID override and multiple live sessions sharing one cwd.
4. Run focused wrapper/Fleet tests, mirror parity, adapter guards, and a dry-run showing the actual thread ID.
5. Commit the task branch, merge to `main`, rerun integrated verification, and push.

## Plan check

- Requirements: fixes the observed orphan cause rather than weakening cwd ambiguity safety.
- Scope: no broker/native-fallback behavior, liveness, or spec semantics change.
- Safety: depth-2 parent metadata remains unchanged; no live child is launched for acceptance.
- Verification: wrapper metadata plus multi-session render behavior are both covered.
