# Dispatch surface terminology v20 — implementation plan

Date: 2026-07-21
Capability / mode / intensity / QA: `autopilot-code` / `dev/refactor` /
`standard+` / `thorough(code)`
Starting branch / HEAD: `depth1-surface-terminology-v2` /
`6f3007b1c65acca02d0348605e9cc32d46c595c4` (`origin/main`)
Worktree: `/home/Uihyeop/agent_setting-wt/depth1-surface-terminology-v2`
Spec significance: `within-spec` — implement the existing PRD v20 §13.12
contract without changing its scope.

## Scope

Implement the approved dispatch terminology and machine contract from a clean
`origin/main` baseline. Do not recover or cherry-pick the deleted candidate or
remediation commits.

- `quick` compiles and runs only as one registered-headless owner node.
- Portable topology uses `dispatch_depth`, `owner_dispatch_depth`, and
  `max_dispatch_depth`.
- Wrapper transport, attempt `execution_surface`, `registered_worker`, and
  `fallback_hop` are distinct validated namespaces.
- Codex native subagent, Claude subagent, Claude agent-team teammate session,
  and registered headless worker session remain distinct concepts.
- `direct` remains inline and unregistered; `standard+` retains the checked
  same-harness headless → cross-harness headless → native-subagent → inline
  fallback recipe.
- Completion markers bind the exact attempt and surface axes. Same-evidence
  retries with different attempt or surface metadata must create distinct
  history and update the canonical marker.
- Multi-capability composition, co-primary routes, cross-capability DAGs or
  envelopes, model selection, and runtime configuration changes are excluded.

## Implementation sequence

1. Update the canonical topology registry/compiler and shared attempt validator.
2. Propagate the qualified schema through route compilation, registry,
   completion, fallback, wrapper CLIs, liveness/progress, and worker guards.
3. Propagate the same model to Fleet and regenerate/mirror adapter surfaces.
4. Add deterministic v20 acceptance tests, including same-artifact retries in
   both registered↔unregistered directions and contextual terminology checks.
5. Run focused suites, the aggregate repository checks, then an independent
   final review. Fix review findings and repeat until the gate passes.
6. Commit the isolated branch, merge it into `main`, verify the integrated
   tree, push `main`, and run guarded worktree cleanup.

## Assurance and execution exception

The selected assurance scope is
`plan-check:selected-independent-pass:final-verify`. A registered headless
owner/stage launch is not used for implementation because the strict worktree
runtime-projection check fails: installed Codex harness links intentionally
point at the primary checkout, not this isolated task worktree. Runtime-owned
links/configuration will not be modified. Implementation therefore runs inline
inside the isolated worktree; any final review is labeled independent only if a
separate checked execution surface actually runs.

## Acceptance

- All new route/registry/completion/Fleet records use qualified dispatch-depth
  fields and exact attempt-surface evidence.
- Unknown namespace values fail closed; legacy versioned records remain
  diagnostic/read-only and cannot be resumed or re-emitted as v20.
- Quick negative fixtures emit no route, row, or process and return the exact
  v20 failure class.
- Same evidence with a different attempt or surface never returns stale marker
  axes.
- Contextual terminology checks reject ambiguous dispatch topology prose while
  preserving Unix `find -maxdepth/-mindepth`, research/search/review depth, UI
  indentation depth, and runtime-native nesting depth.
- Canonical/generated/adapter parity checks and Fleet tests pass.
- No composition/co-primary contract is introduced.

