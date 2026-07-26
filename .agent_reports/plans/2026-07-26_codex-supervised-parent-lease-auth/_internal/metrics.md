# Pipeline metrics and exceptions

- route: `autopilot-code · debug/standard · standard QA`.
- secondary route: `autopilot-spec · update`.
- spec-significance: `SPEC-SIGNIFICANT` (SD-72/77/78 parent-liveness evidence).
- self-hosting exception: `STAGE_DISPATCH_INLINE_OK=dispatch-infra-self-modification`.
- inline reason: the exact depth-1→depth-2 launch gate being repaired currently
  rejects this App Server owner before child spawn; no independent stage claim
  is made until a post-fix registered smoke actually starts.
- scope exclusions: hook trust review warning; OpenCode
  `opencode-standard-depth2-unsupported`; unrelated stale drill rows.
- initial failed attempt: `att-f71ac671244a489aade65654f0dcc499`.
- initial child result: `child_spawned=0`,
  `parent-attempt-not-live` / `direct-auth-check:auth-unavailable`.

## Verification evidence

- focused deterministic suites: 52 dispatch-contract, 3 Codex App Server
  supervisor, 12 lifecycle, 8 nested-auth, 5 orphan-watch, 22 Codex wrapper,
  and 11 adapter integration tests passed.
- broad dispatch checks: liveness matrix, readiness, completion join, harvest,
  parent context/park, dispatch-node/batch/registry/progress/fallback, Fleet, and
  dispatch-v20 conformance passed.
- repeated real auth eligibility: 10/10 `supported` with
  `direct-auth+headless-check`.
- bounded live smoke: owner `att-3fedfb87bf9942c7a8c2c701c02509af`
  started child `att-ac2d63c649184f38a812b684771a8932` with
  `child_spawned=1`, `parent_liveness_source=supervisor-lease`, and internal
  nested eligibility `supported`; exact completion, resume, harvest, liveness,
  lease cleanup, state cleanup, and process quiescence passed.
- post-rebase verification on current `origin/main`: 52 dispatch-contract,
  3 supervisor, 12 lifecycle, 8 nested-auth, 5 orphan-watch, 22 Codex wrapper,
  11 adapter integration, 8 dispatch-v20, 22 batch, 10 completion-join,
  26 node, 37 registry, 10 liveness-matrix, 3 parent-context (34 captures),
  15 progress, and 35 capability-route tests passed. Shell liveness,
  adaptation-boundary, and 29 generated-projection tests also passed.
- baseline-only generator drift remains outside this branch:
  `tools/generate.py --check` reports stale `post-it` manifest/catalog/Skill
  projections; none of its reported paths differ from `origin/main` on this
  branch. This task did not regenerate or import those unrelated files.
- integration: rebased without conflict onto `origin/main` at `6c68e900` while
  preserving the new n-way `parallel_group` contract. Commits `379164fe` and
  `78b79561` were pushed to
  `origin/fix/codex-supervised-parent-lease-auth`.
- merge authorization and recheck (2026-07-27): current `origin/main` remained
  the exact ancestor of `78b79561`; 52 contract, 3 supervisor, 8 nested-auth,
  11 adapter, 22 batch, 12 lifecycle, 5 orphan-watch, and 29 generated-
  projection tests passed immediately before the main fast-forward.
- merge scope: only the two feature commits, stage-dispatch v31 transaction,
  and curated cycle evidence are integrated. Unrelated root-spec/plan/review
  changes and raw App Server/session logs remain unstaged.
