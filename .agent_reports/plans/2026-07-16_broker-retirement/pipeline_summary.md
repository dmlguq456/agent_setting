# Broker Retirement Pipeline Summary

Status: source integrated; report commit and push pending

- Spec: stage-dispatch PRD v15 (`b50e4524`)
- Decision: broker retired from new routes; direct nested headless becomes primary.
- Compatibility: v1/v2 verify/Fleet read only; register/start fail closed.
- Runtime evidence: recursive Codex headless succeeded only after the depth-1 owner received network access plus a worktree-local writable `CODEX_HOME` projection.
- Verification: integrated portable guards 368/0, Fleet 565/0, Claude mirror dispatch 69/0, adaptation boundary PASS; independent verifier found no merge blocker.
