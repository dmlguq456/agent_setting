# Pipeline summary — Worker bootstrap / role boundary

## Result

The registered-session bootstrap, assigned Skill, and model/subagent role
namespaces are now independent. Canonical route writers emit
`worker_type` + `assigned_contract` + `model_role` and do not synthesize
`worker_role`. Old rows remain readable.

## Fleet behavior

- Depth 1 gets its owner label from `worker_type=owner`.
- Depth 2 shows `assigned_contract` when it is a real child Skill, then falls
  back to `route_node` or the registry capability.
- Internal personas and model-role strings no longer become stage identity.

## Verification snapshot

- Worker/bootstrap/dispatch focused tests: PASS.
- Canonical Fleet: 722/722 PASS.
- Focused Fleet + mirror parity: 117/117 PASS.
- Concurrency dispatch fixture: PASS.
- Adaptation boundary: PASS.
- Manifest and `git diff --check`: PASS.
- Runtime doctor and strict runtime doctor: PASS when run sequentially.
- Drill execution intentionally not run under the repository policy; migrated
  fixture/assert shell files pass syntax validation.

The commit hash and push result are reported in the user handoff.
