# Capability routing topology v9 — pipeline summary

Implemented the approved vertical slice across portable core, capability registry, adapter dispatch surfaces, detached/resource safety, model-worker governance, lab smoke/report contracts, and identifier-aware synchronization.

Changed surfaces: `core/`, `capabilities/`, `utilities/`, `tools/`, `hooks/`, `loops/`, and generated Claude/Codex/OpenCode projections.

Verification evidence is in `test_logs/verification-summary.md`; implementation notes are in `dev_logs/implementation.md`. The installed runtime projection mismatch and unavailable registered nested worker transport are recorded limitations, not source-test failures.

## Verification commands

- `python3 tools/capability_topology.test.py`
- `python3 utilities/capability_route.test.py`
- `python3 utilities/model_worker_governor.test.py`
- `python3 utilities/resource_runner.test.py`
- `python3 tools/smoke_attestation.test.py`
- `python3 tools/report_manifest_verify.test.py`
- `bash hooks/spec-sync-nudge-v9.test.sh`
- three adapter `dispatch-headless.sd15.test.sh` suites
- `python3 tools/build-manifest.py --check`
- `python3 tools/generate.py --check`
- `bash tools/generated-projections.test.sh`
- `bash tools/skill-conformance/check.sh`
- `bash tools/check-adaptation-boundary.sh`
- `bash tools/routing-contract.test.sh`
- `python3 tools/context-footprint.py --strict`
- full `hooks/portable-guards.test.sh` through the Codex verification runner (`PASS=357 FAIL=0`)
- Fleet title refresh/cross-harness/mirror test modules (60 tests)
- shell syntax, Python compile, route-row/completion, detached process, and `git diff --check` checks

## Unsupported runtime contracts

- Registered Codex depth-2 workers cannot initialize the in-process app-server in this read-only worker sandbox.
- Registered Claude verifier/reporter rows started but exited before producing a turn or report. They are closed as `dead-empty-runtime`; independent QA is not claimed.
- Runtime projection diagnostics target the installed primary checkout. This branch did not mutate user-owned runtime configuration.

## Integration status

- The main orchestrator rebased the worktree onto `origin/main@e7a43a65`, resolved the final shared-governor test isolation regressions, and pushed commit `26497cd0` to `origin/capability-routing-topology`.
- After explicit user authorization, the source branch and canonical v9 spec artifacts were integrated into `main` by merge commit `cdf24f27`.
- Integrated verification repeated the full portable guard (`PASS=357 FAIL=0`) plus generated projection, Skill, routing, topology, governor, resource, smoke, report, strict context, adaptation-boundary, and diff checks.
- No runtime-owned Codex configuration or installed projection was changed.
