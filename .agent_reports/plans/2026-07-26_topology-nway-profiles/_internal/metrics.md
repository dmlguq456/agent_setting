# Execution metrics and exceptions

- route: `autopilot-code/dev/strong`
- spec-sync: `autopilot-spec/update`
- tracking: `tracked`
- dispatch exception: `dispatch-infra-self-modification`
- reason: this cycle changes the route compiler, batch admission, governor, and
  wrapper contract that a standard+ owner would use to execute the same cycle.
  Source work therefore runs in the isolated task worktree with the current
  session as integrator; no claim of registered stage-dispatch participation is
  made. The completed implementation is verified through deterministic batch,
  route, wrapper, and projection fixtures before runtime adoption.
- official runtime check: Codex manual refreshed 2026-07-26; Claude Code model,
  effort, and subagent documentation checked 2026-07-26.
- compiled route: `rt-603b029d28c9b6c3`, registry
  `sha256:85d67a79be93cff7fcc053e794728ddd387dc83bc88e872cbefe9f3bfde3bc7b`,
  owner profile `deep`, groups `frame=3`, `plan=2`, `impl-review=2`.
- profile resolution: Claude/Codex expose four distinct profiles; OpenCode
  records `balanced-deep -> deep` as reduced granularity. Fable is main-only.
- focused verification: topology 20, route 35, profile 6, batch 22, governor
  21, dispatch contract 49, dispatch node 26, fallback 12, completion join 10,
  route guard 13, adapter wrappers 48 — all PASS.
- broad verification: the isolated worktree Fleet run passed 875 tests and
  portable guards passed 358 checks. Generated projections, manifest,
  model-config, adaptation boundary, runtime projection, dispatch
  lifecycle/concurrency/registry suites, and `git diff --check` passed.
- integrated-primary verification: runtime projection and 356 topology-focused
  tests passed. A repeated full Fleet run exposed one pre-existing
  `token_accounting` timestamp-order race (`1/875`); the topology diff does not
  touch either accounting mirror. This is recorded separately, not counted as a
  topology failure or silently reported as an integrated full-suite pass.
- independent audit: no blocker. Remaining `replica_*` identifiers are limited
  to explicit one-window v1 read/CLI compatibility and compatibility fixtures.
- source integration: commit `9c0b9e2e`, branch and `main` pushed, fast-forward
  integrated, guarded worktree cleanup returned `status=removed`.
