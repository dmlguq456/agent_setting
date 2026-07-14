# Final report

Status: complete and merged to `main`.

Worker worktrees are now source-only. Durable agent output is resolved to the
primary checkout's canonical artifact root, and explicit worker-local artifact
writes fail closed. Claude, Codex, and OpenCode all receive the same invariant
through runtime-native scoped access.

Worktree cleanup is available as a fail-closed main/orchestrator step after
merge, integrated verification, and push. It preserves branches, never uses
force, refuses dirty/unmerged/unpushed/locked/active targets, reconciles stale
registry rows only after eligibility is proven, and records a bounded audit.
Runtime session-end events remain non-authoritative.

The implementation was validated, pushed, fast-forwarded into main, and the
feature worktree was removed with the new cleanup path. Unrelated unmerged
worktrees were left untouched.
