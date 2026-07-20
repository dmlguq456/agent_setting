# Cycle metrics and dispatch exception

- Requested route: `autopilot-code`, `dev/refactor`, intensity `strong`, QA `standard`.
- Expected graph: `code-plan -> code-execute -> code-test -> code-report`.
- Registered planning attempts: 3.
- Successful registered planning artifacts: 0.
- Failure signature: child Codex processes terminated during startup or initial
  Skill read, without a typed three-line handoff or durable plan.
- Native subagent use: 0 (not authorized by active system contract).
- Inline exception: planning, execution, testing, and reporting continue in the
  root acting owner after registered runtime exhaustion.
- Compensating assurance: durable plan, inline plan-check, locked spec update,
  focused concurrency/authority tests, repository contract regressions, final
  diff inspection, and post-merge verification.
- Starting source after moving-base reconciliation:
  `f9aba3969bca3de6b668972f3819d36cfc614165`.
- Accepted target commit: `8ceb3cbda6578dd...` (selective port).
- Rejected target commit: `35a0c75d6af1c0581451772956b40ff342dd7d17`
  (archive only).
