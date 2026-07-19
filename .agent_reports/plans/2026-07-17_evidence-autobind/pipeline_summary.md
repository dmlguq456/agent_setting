# Evidence autobind — pipeline summary (OPERATIONS §5.8)

## Route and scope

- capability `autopilot-code`, mode `dev`, intensity `standard`, QA `standard`, depth 2.
- route_id `rt-babd26fbb4f65d1b`, dispatch_contract_version 3.
- spec-significance: within-spec — `spec/stage-dispatch/prd.md` §13.7.6 + acceptance ③.
- worktree: `/home/Uihyeop/agent_setting-wt/evidence-autobind`, branch `evidence-autobind`, base `origin/main@5972a61d`.
- write scope: source edits confined to `utilities/dispatch-node.py` and the three adapter wrappers (`adapters/{claude,codex,opencode}/bin/dispatch-headless.py`) plus their test files; `spec/**`, `capability-route.py`, dispatch-defaults semantics, authorization classifier, broker remnants, and the g10 drill fixture were out of scope and confirmed untouched.

## Stage-by-stage

| Stage | Harness | Verdict | Artifact |
|---|---|---|---|
| plan | codex | PASS | `plan.md`, `checklist.md` |
| execute | claude | PASS | `dev_logs/execute.md`, commit `1685cd3d` on worktree HEAD |
| test | codex | **FAIL** | `test_logs/test.md` |
| report | claude | FAIL (this artifact) | `pipeline_summary.md`, `final_report.md` |

## What landed

Commit `1685cd3d4cffb9129abc4b8c89b4558da241b58b` on branch `evidence-autobind` (base `5972a61df915815a71b818fec83794a913e2e23e`), not merged, not pushed:

- `utilities/dispatch-node.py`: refactored into `select_checked_tuple`, `bind_dispatch_evidence`, `collect_explicit_evidence`, `strip_leading_separator` + `DispatchNodeError`. For depth-2 route nodes, deterministically selects a checked `dispatch_fallback` candidate, cross-checks it against top-level `route.dispatch_evidence.tuples`, and forwards the six/seven required evidence flags to the wrapper. Explicit caller values that match are passed through without duplication; explicit/record conflicts raise `DispatchNodeError` before wrapper invocation. Depth-1/resource-runner nodes are untouched.
- `adapters/{claude,codex,opencode}/bin/dispatch-headless.py`: added `bind_internal_eligibility_probe(args)`, triggered only when evidence is absent at depth-2 `start` with known parent identity. Runs `utilities/nested-dispatch-eligibility.py --json` in-wrapper and binds the returned identity-matching row; sets `eligibility_probe=internal` provenance in success and failure output/jobs pipe.
- New `utilities/dispatch_node.test.py` (17 tests) and expanded `adapters/*/bin/dispatch-headless.sd45.test.py` (+8 tests each, 24 total new).

## What was verified — real command verdicts (from `test_logs/test.md`)

- `python3 -m py_compile <all 9 changed/new files>` — PASS
- `python3 utilities/dispatch_node.test.py` — PASS, 17 tests
- `python3 utilities/dispatch_contract.test.py` — PASS, 10 tests
- `bash adapters/{claude,codex,opencode}/bin/dispatch-headless.sd15.test.sh` — PASS (5/8/7 checks)
- `python3 adapters/{claude,codex,opencode}/bin/dispatch-headless.sd45.test.py` with inherited `AGENT_DISPATCH_JOBS` — 1/9 fails each, rc 73; with `env -u AGENT_DISPATCH_JOBS` — PASS, 9 tests each. Reproduced identically against a `git archive 5972a61d` base copy → confirmed pre-existing, environment-shaped (nested-worker `AGENT_DISPATCH_JOBS` inheritance colliding with the test's own `--jobs` fixture under SD-49), not a regression introduced by `1685cd3d`.
- `python3 utilities/stage_dispatch_fallback.test.py` — PASS, 7 tests
- `python3 utilities/nested_dispatch_eligibility.test.py` — PASS, 4 tests
- `bash utilities/dispatch-route.test.sh` — PASS
- `git diff --exit-code 5972a61d..HEAD -- loops/drill/cases_growing/g10_claude_opencode_depth2_start spec` — PASS, both forbidden trees untouched
- `git diff --check 5972a61d..HEAD` — PASS
- Adversarial gate-weakening audit (test stage, independent of the above regression suites) found 3 confirmed contract defects (see `test_logs/test.md` "Defects" and `final_report.md`):
  1. wrappers bind `status=supported` from probe JSON without checking `subprocess.run(...).returncode`, so a probe that exits 69 with identity-matching "supported" JSON is accepted as launchable evidence — reproduced against all 3 wrappers.
  2. explicit `--nested-eligibility unknown` is indistinguishable from the parser default and gets silently overwritten by a successful internal probe.
  3. `bind_dispatch_evidence` only compares `--eligibility-failure-class` when the record's value is non-empty, so an empty-record/non-empty-explicit conflict is not caught.
- Residual risk (unconditional depth-2 binding regardless of `--action`) was assessed by the test stage as acceptable under current `capability-route.py` compile/verify invariants, not a present defect.

## Terminal state

**FAIL.** The test stage's gate-weakening audit found 3 confirmed contract defects in the committed implementation; overall verdict in `test_logs/test.md` is FAIL. Per the task brief, the execute node is pinned to `source_commit 5972a61d` and worktree HEAD has moved to `1685cd3d`, so a same-cycle execute redispatch is structurally rejected by worker-route-guard, and `git reset --hard` is forbidden. This cycle closes FAIL with an ordered fix-forward list (see `final_report.md`) for depth-0 main rather than retrying in-cycle.

## Safety state

- All work is confined to the task worktree (`/home/Uihyeop/agent_setting-wt/evidence-autobind`) and branch `evidence-autobind`.
- One implementation commit (`1685cd3d`) on top of the base pin (`5972a61d`); no merge to main, no push to any remote.
- No source file outside the approved write scope was touched; `spec/**` and the g10 drill fixture are byte-identical to base, confirmed by `git diff --exit-code`.
- No fixes were applied and no source was edited during this report stage, per assignment.
