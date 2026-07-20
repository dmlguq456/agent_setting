# Plan — Worker bootstrap / assigned Skill / model role boundary

spec-significance: within-spec — this implements the existing portable
main/worker bootstrap separation and Fleet assigned-skill contract. The
concurrently edited stage-dispatch v20 transaction is not modified.

## Problem

Canonical route writers passed topology `node.kind` or model-role text through
the legacy `worker_role` field. The bootstrap helper then inferred both
`worker_type` and the assigned stage contract from that overloaded value.
Fleet also had to guess session type and stage identity from the same string.

## Contract

- `worker_type`: selects exactly one owner/stage/review/support bootstrap.
- `assigned_contract` plus `route_node`: identifies the worker's Skill or
  bounded route assignment.
- `model_role`: selects the portable model profile.
- `worker_role`: legacy read compatibility only; canonical writers omit it and
  prompts do not expose it as identity.

## Implementation

1. Map topology kinds directly to worker types in route-node and fallback
   dispatch writers.
2. Resolve an assigned contract from an explicit value or a completion gate
   that exists in the portable capability catalog; otherwise retain the entry
   contract and narrow it with the immutable route node.
3. Project the three authoritative fields independently through all adapter
   prompts, registries, and child environments.
4. Teach Fleet to collect `worker_type` and `assigned_contract`, display the
   exact assigned Skill, and use legacy `worker_role` only as a final fallback.
5. Migrate dispatch guidance and drill fixtures so new rows with
   `worker_role` fail the boundary check.

## Verification

- Worker bootstrap, prompt, route-node, fallback, and concurrency tests.
- Canonical Fleet full suite and focused Claude mirror suite.
- Portable guard suite, runtime doctor, mirror parity, manifest, adaptation
  boundary, and `git diff --check`.
- Do not execute drill automatically; validate drill shell syntax and keep the
  drill assertions as the next explicit runtime exercise.
