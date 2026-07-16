# Verification

## PASS

- `python3 utilities/worker_bootstrap.test.py` — 5 tests
- `python3 utilities/worker_dispatch_prompt.test.py` — three adapters, custom
  assignment, one kernel/type, exact handoff
- `python3 utilities/dispatch_adapters_v11.test.py`
- `python3 utilities/dispatch_completion_marker.test.py` — 4 tests
- `python3 utilities/dispatch-artifact-root.test.py` — 3 tests
- three `dispatch-headless.sd45.test.py` route-consumer suites
- three `dispatch-headless.sd15.test.sh` early-death/liveness suites
- all six `tools/profile/build-home.py <profile> --check`
- code-test profile instance smoke + `tools/install/profile-activation.test.sh`
- `tools/generated-projections.test.sh`
- `tools/skill-conformance/check.sh`
- `tools/check-adaptation-boundary.sh`
- `python3 tools/context-footprint.py --root . --strict`
- `adapters/codex/bin/check-runtime-projection.sh`
- Codex and OpenCode `preflight.sh doctor --runtime`

## Baseline-known unrelated failure

`tools/routing-contract.test.sh` reports the same three failures on pre-change
main: compact Codex `autopilot-lab`/`autopilot-refine` bodies omit two expected
headings and the Claude bootstrap omits a literal `WORKFLOW §0.2` string. This
cycle does not modify those three surfaces; worker-bootstrap-specific routing,
route-record, profile, and adapter assertions pass.

## Footprint

| Surface | UTF-8 bytes |
|---|---:|
| kernel | 1,571 |
| owner | 2,028 |
| stage | 1,906 |
| review | 1,878 |
| support | 1,862 |

These are static input sizes, not token, billing, savings, cost, or ROI claims.
