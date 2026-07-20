# Fleet / Dispatch Terminal Reliability

## Objective

Ensure a Codex sandbox-initialization failure closes the exact registered
attempt, advances the checked fallback on the same route, and cannot be revived
by another session's transcript. Make an interactive Codex session become idle
immediately after its exact `task_complete` or `turn_aborted` event.

## Scope

1. Validate the nested transport vocabulary and worktree `.codex` mount shape
   before registration or spawn.
2. Parse an exact foreground Codex transcript after process exit and close a
   terminal `BLOCKED` sandbox-init attempt with `dead-sandbox-init`.
3. Treat `process-exited` as a fallback condition until a completion marker or
   typed terminal row proves success.
4. Keep exact namespace-local attempt evidence authoritative over cwd-wide
   transcript activity in Fleet and Codex liveness.
5. Preserve one immutable route through checked inline fallback; add defensive
   current-attempt selection only where existing lineage metadata is present.
6. Apply the existing Codex task lifecycle parser to ordinary sessions, using
   mtime only when lifecycle evidence is unavailable.

## Verification

- Unit fixtures for a tracked empty `.codex` file and noncanonical transport.
- Foreground exit-0 transcript containing `turn.completed` plus `BLOCKED`.
- Namespace-local launch heartbeat followed by exact process-exit evidence.
- A fresh unrelated owner transcript must not make the failed child `ALIVE`.
- Same-route fallback remains selected and the failed attempt has no open row.
- Interactive `task_complete` bypasses the mtime working window and hysteresis.
- Existing foreground completion-marker race tests remain green.
- Fleet canonical/mirror parity and relevant dispatch/Fleet suites pass.
