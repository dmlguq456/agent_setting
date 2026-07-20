# Checklist

- [x] Confirm the topology already separates kind, role, node, and gate.
- [x] Make `worker_type` authoritative for session bootstrap.
- [x] Add `assigned_contract` to adapter prompt, registry, and child env.
- [x] Stop canonical route/fallback writers from synthesizing `worker_role`.
- [x] Keep legacy `worker_role` parsing without giving it precedence.
- [x] Add Fleet fields and authoritative display precedence.
- [x] Update owner display to use `worker_type=owner`.
- [x] Update dispatch instructions and three-harness help.
- [x] Convert drill fixtures/assertions to the separated fields.
- [x] Run focused dispatch and Fleet regressions.
- [x] Run full canonical Fleet suite and adaptation boundary.
- [x] Run final diff/manifest and adaptation-boundary checks.
- [x] Prepare a selective commit scope that excludes concurrent stage-spec work.
