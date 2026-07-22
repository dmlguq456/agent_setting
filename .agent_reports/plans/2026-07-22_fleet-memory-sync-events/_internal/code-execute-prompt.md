This is only route node `execute`, assigned contract `code-execute`, for `rt-d7392fcfbc9ce241`. Do not route, review your own work as independent, commit, merge, push, or edit canonical specs.

Implement the approved plan in `/home/Uihyeop/agent_setting-wt/fleet-memory-sync-events`. Read the cycle `plan.md`, `checklist.md`, plan-check PASS artifact, D-37 v22, Fleet F-19/F-35f v15, and the research/review evidence.

Required behavior:

- Newly INSERTed migrate/sync absorption emits exactly one journal row with `action=add`, literal `actor=sync`, and the logical source cwd when known.
- Existing-source, source-upsert, and body-dedup reinforcement paths emit no absorption event; repeat sync is idempotent.
- Auto-memory uses decoded encoded-project cwd; post-it uses repo root; valid legacy origin may provide cwd; global/decode-impossible sources omit cwd with no fallback.
- Existing manual add/note and all other journal callers retain current action/actor/cwd behavior.
- No historical journal rewrite or user runtime-store mutation.

Use additive, explicit API parameters with an unambiguous sentinel where required; grep every caller before changing signatures. Run `preflight.sh write` before every source/test edit and use `apply_patch`. Add deterministic isolated tests for hostile ambient env, exact one-event creation, repeat zero, dedup zero, no-backfill sentinel preservation, cwd omission, and Fleet grouping under an `agent-note`-like repo key. Do not change the collector merely to make a redundant test pass.

Write implementation evidence to `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-memory-sync-events/dev_logs/execute.md`, update `checklist.md`, run focused syntax/tests, complete the exact `execute` marker/attempt, and return the kernel's exact three-line handoff. Leave the source diff uncommitted for the main integrator.
