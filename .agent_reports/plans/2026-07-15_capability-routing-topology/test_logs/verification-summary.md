# Verification summary

PASS:

- New registry, route, governor, detached runner, smoke, report-manifest, and spec-nudge tests.
- Route/node dry-run, route metadata registry row, and stale completion rejection.
- Three adapter SD-15 dispatch tests and low-level dispatch-route compatibility.
- Manifest/generator checks, generated projections, four-tree Skill conformance, routing contract, adaptation boundary, shell/Python syntax, strict context footprint, and Fleet title tests (60 tests).
- Detached process start/status/stop with current smoke attestation.
- Full portable guard integration after rebase: `PASS=357 FAIL=0`.
- Final branch state is clean and pushed at `26497cd0`.
- Integrated `main` repeated the full portable guard (`PASS=357 FAIL=0`) and all focused generator/routing/topology/governor/resource/smoke/report/context/adaptation checks before push.

Diagnostic-only limitation:

- Runtime projection check correctly reports that the installed user-owned Codex projection targets the primary checkout, not this linked worktree. No runtime config or links were changed.
- Registered depth-2 Codex planning failed before a turn because the in-process app-server could not initialize on a read-only runtime path; Claude fallback exited before producing a turn. Independent registered QA is therefore not claimed.
