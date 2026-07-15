# Checklist

- [x] Read v12 PRD, governing core contracts, official Claude/Codex runtime surfaces, and current v11 implementation.
- [x] Create isolated source worktree from pushed v12 spec commit.
- [x] Implement deterministic broker protocol and lifecycle.
- [x] Route all depth-2 headless fallback attempts through the broker.
- [x] Wire preflight/lifecycle readiness and immutable endpoint/jobs binding.
- [x] Add 4-placement and fault/idempotency tests.
- [x] Run focused and repository parity checks; fix regressions.
- [x] Commit branch, merge to main, verify integrated tree, push, and clean worktree.
- [x] Complete dev/test logs and pipeline summary.

## Out of scope

- [x] O2 not implemented.
- [x] O3 not implemented.
