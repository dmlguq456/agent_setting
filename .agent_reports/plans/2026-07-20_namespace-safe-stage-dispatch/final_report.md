# Namespace-safe stage dispatch — final report

## Outcome

Depth-1 Codex owners can now launch registered depth-2 Codex or Claude stage
workers from a transient tool-call PID namespace. `dispatch-chain` selects
`foreground-scoped`, the wrapper supervises the child through terminal exit,
and durable scopes retain the prior detached behavior.

Fleet no longer silently drops a depth-2 row when its recorded parent slug is
missing or stale: it renders the row as an orphan. Future launches avoid that
condition by exporting the wrapper's exact self slug, defaulting the logical
parent from it, and rejecting explicit parent mismatch before registration.

## Runtime boundary

- Foreground Codex children under a checked Codex `workspace-write` owner disable
  only the nested inner mount sandbox; the outer sandbox remains authoritative.
- Standard+ Codex owners expose only existing `.core-grounding` and Claude
  `session-env` scratch directories in addition to established writable roots,
  enabling adapter guards and Claude Bash without widening runtime homes.
- Native subagents remain a distinct fallback surface; Codex↔Claude registered
  headless dispatch parity is preserved.

## Evidence

- Live Claude depth-2 PASS:
  `_internal/plan_reviews/live_claude.md`.
- Live Codex depth-2 PASS with 66 focused checks:
  `_internal/plan_reviews/live_codex.md`.
- Final deterministic suites and adaptation boundary: PASS.
- Stage-dispatch component spec: v19, snapshot v18, transaction route
  `rt-94ed270212e80967`.
