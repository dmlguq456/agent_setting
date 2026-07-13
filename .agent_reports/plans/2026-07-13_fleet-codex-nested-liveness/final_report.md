# Final report

## Verdict

PASS — Fleet and the Codex liveness helper now discover nested dispatch transcripts stored in a conductor worktree's local `CODEX_HOME`.

## User-visible effect

An active non-profile depth-2 Codex stage is no longer misclassified as dead merely because Fleet itself runs under another `CODEX_HOME`. Its depth-1 owner and depth-2 child remain visible as working rows. Profile isolation and dead-row folding semantics are unchanged.

## Evidence

- Fleet full suite: 177 PASS.
- Codex SD-15/liveness suite: PASS.
- Current real registry and rollout path: depth-1 working; actual depth-2 row replay working under its parent.
- Mirror parity, syntax, and diff checks: PASS.
