This is only route node `plan` (`code-plan`) for `rt-d7392fcfbc9ce241`. Do not edit source, specs, tests, or dispatch another worker.

Create the durable implementation plan and checklist for the Fleet memory sync-event attribution fix. Authoritative inputs:

- worktree `/home/Uihyeop/agent_setting-wt/fleet-memory-sync-events` at sealed commit `e8938809d87e54474f5e7242a2552598c2636a0a`;
- route `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-memory-sync-events/_internal/code-route.json`;
- root PRD D-37 v22 and Fleet PRD F-19/F-35f v15 under `/home/Uihyeop/agent_setting/.agent_reports/spec/`;
- research `/home/Uihyeop/agent_setting/.agent_reports/shards/spec-research/fleet-memory-sync-events/research.md`;
- review `/home/Uihyeop/agent_setting/.agent_reports/reviews/spec/fleet-memory-sync-events/verdict.md`.

Plan a minimal additive implementation in `tools/memory/mem.py` and focused tests. It must:

- journal only a newly INSERTed migrate/sync record, never existing-source skip, source upsert, or body-dedup reinforcement;
- emit existing `action=add` with literal `actor=sync`, ignoring ambient `MEM_ACTOR`, `MEM_DISTILL`, `MEM_CWD`, and process cwd for attribution;
- carry an explicit per-event logical cwd override while preserving existing callers' fallback behavior; explicit missing cwd must omit the field rather than fall back;
- derive auto-memory cwd by decoding its encoded project directory, post-it cwd from the registered repo root, legacy cwd only when validly decoded, and omit cwd for global/decode-impossible sources;
- remain prospective-only with no real journal backfill;
- prove idempotent repeat sync, body-dedup no-event, hostile-env attribution, and Fleet `by_repo` grouping for an `agent-note`-like source;
- keep `tools/fleet/collectors/memory.py` unchanged unless a failing acceptance test demonstrates a real consumer gap.

Include caller/signature analysis, exact test files/commands, projection/parity checks, rollback risks, and the linked-worktree no-commit boundary. Write only:

- `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-memory-sync-events/plan.md`
- `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-memory-sync-events/checklist.md`

Complete the exact `plan` marker/attempt and return the kernel's exact three-line handoff.
