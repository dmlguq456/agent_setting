# Topology N-way profiles — final report

## Outcome

Implementation, verification, main integration, push, and guarded worktree
cleanup are complete.

## Delivered contract

- Four execution profiles: `deep`, `balanced-deep`, `light`, `mini`.
- Light defaults to medium effort; balanced-deep uses the deep tier at medium.
- Mini is limited to lifecycle or explicitly micro-semantic helpers and is
  rejected for substantive registered owners, stages, and reviews.
- Parallel groups are route-declared, asymmetric, exact-size 2–4 sibling sets.
- Cross-harness diversity is primary; model-profile and perspective diversity
  are sealed as additional axes.
- Initial admission is all-or-zero. A one-leg recovery requires exact N-1 peer
  receipts and route-bound identity.
- Dispatch depth 3 remains forbidden.

## Verification evidence

Focused suites passed: topology 20, route 35, profile 6, batch 22, governor 21,
contract 49, node 26, fallback 12, completion join 10, route guard 13, and the
three adapter wrapper suites 48. The isolated worktree full Fleet suite passed
875 tests and portable guards passed 358 checks. Generated projections,
manifest, model configuration, adaptation boundary, mirror parity, dispatch
lifecycle/concurrency/registry suites, and `git diff --check` passed.

After fast-forward integration, runtime projection and 356 topology-focused
tests passed on the primary checkout. The integrated full Fleet rerun exposed
one pre-existing failure in
`test_store_rejects_extra_fields_and_serializes_concurrent_updates`: timestamp
values are sampled before the directory lock, so acquisition order can make
`last_observed_at` precede `first_observed_at` and reset the aggregate. The
topology commit changes neither `tools/fleet/token_accounting.py` nor its Claude
mirror. This unrelated race is reported explicitly and was not patched under
the topology scope.

The independent audit found no blocker. Legacy `replica_*` names remain only as
one-window v1 readers/CLI aliases and compatibility fixtures; canonical writes
use `parallel_group`.

## Route evidence

- code route: `rt-603b029d28c9b6c3`
- spec route: `rt-a3aae3b053d5c8b7`
- registry digest:
  `sha256:85d67a79be93cff7fcc053e794728ddd387dc83bc88e872cbefe9f3bfde3bc7b`
- strong owner profile: `deep`
- strong groups: frame 3, plan 2, implementation review 2

## Integration

- source commit: `9c0b9e2e` (`feat(topology): add profile-sealed n-way dispatch`)
- branch push: `origin/topology-nway-profiles`
- main integration: fast-forward, pushed to `origin/main`
- runtime projection: PASS on the primary checkout
- cleanup: `status=removed`, no active PID or stale registry row
