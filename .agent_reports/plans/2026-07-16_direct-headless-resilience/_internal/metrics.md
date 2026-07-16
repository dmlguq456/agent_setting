# Pipeline metrics and runtime-contract record

- Route: `autopilot-code`, `dev/backend`, standard intensity, thorough QA.
- Stage graph: `code-plan -> code-execute -> code-test -> code-report`.
- Priority completed: `SD-58 -> SD-59 -> SD-60`.
- Shared classifier: `tools.fleet.model.classify_attempt_evidence`.
- Direct recursive smoke: root -> Codex depth-1 owner -> Codex depth-2 stage.
- Selected smoke hop: `same-harness-headless`; launch authority `conductor`;
  `broker_lifecycle=retired`; stage attempt
  `att-09f636ba2c930e713bb539651d339a62ef4e60802f30d631`.
- Smoke heartbeat: launch/analysis/tool/terminal, final sequence `4`.
- Namespace finding: child PID `437` was namespace-local; fixed with
  `pid_scope=namespace-local` and exact route-attempt heartbeat classification.
- Independent verifier: PASS; five targeted repros closed; no blocker.
- Fleet: 569 tests passed.
- Focused counts: SD-58 10, SD-59 6, SD-60 8, fallback 7,
  contract 10, nested eligibility 4, worker prompt 2, adapter v11 6.
- Broker/spool/daemon additions: `0`.
- Runtime projections: Claude, Codex, and OpenCode linked activations fresh at
  source revision `5fbace3e` before final artifact commit.
- Source commits: `821405f3`, `3b9622a2`, `f59163e8`.
- Main merges: `7480c5bc`, `8d51304d`, `5fbace3e`.
- Artifact completion commit: `32d399a1` plus the final cleanup-status update.
- Push: `origin/main` advanced through the completion artifacts.
- Cleanup: `direct-headless-resilience` and `broker-retirement` removed as
  eligible; dirty `fleet-depth2-retry-liveness` preserved without mutation.
