# Pipeline summary

> slug: `2026-07-13_readme-product-surface` · graph: `code-plan -> code-execute -> code-test -> code-report` · verdict: PASS with environment notes

## Changed files

- Landing/docs: `README.md`, `MANUAL.md`, `capabilities/README.md`, `core/ADAPTATION.md`, `core/CONVENTIONS.md`, Claude bootstrap/oncall/editorial docs.
- Retired: `capabilities/sync-skills.md`, `skills/.sync_state.json`, portable/Claude/Codex/OpenCode `sync-skills` trees and command/plugin projections.
- Deterministic ownership: `tools/build-manifest.py`, `tools/check-adaptation-boundary.sh`, `tools/skill-conformance/check.sh`.
- Synced/generated: Claude plugin projections, Codex native mode/plugin/skill projections, OpenCode native skill/command projections, `manifest.json`.
- Fixtures/counts: fleet dispatch fixtures, portable guard fixture, Claude installer advertised skill count.

## Verification commands and results

All concrete commands ran through `adapters/codex/bin/preflight.sh verification-runner`.

- PASS: Python AST/import checks; README link/order and installer help/dry-runs; active-reference and retired-path census; `git diff --check`.
- PASS: `python3 tools/build-manifest.py --check`.
- PASS: `adapters/claude/bin/sync-native-plugin.py --check`.
- PASS: Codex `sync-native-{skills,plugin,agents,modes}.py --check`.
- PASS: OpenCode `sync-native-{skills,commands,agents}.py --check`.
- PASS: `tools/check-adaptation-boundary.sh`; `tools/skill-conformance/check.sh`; `adapters/codex/bin/preflight.sh doctor`.
- PASS: `hooks/portable-guards.test.sh` — 343 checks.
- PASS: root and Claude fleet dispatch suites — 58 tests each, byte-equivalent fixtures.
- PASS: isolated HOME `./tools/install/harness.sh install all --yes --json` then `verify --json` across Claude/Codex/OpenCode.
- PASS: worktree Codex runtime projection install and `doctor --runtime`.

## Artifacts

- `plan.md`, `checklist.md`
- `_internal/metrics.md`, `_internal/plan_reviews/risk-review.md`
- `dev_logs/implementation.md`
- `test_logs/test_report.md`
- `final_report.md`, `pipeline_summary.md`

## Unsupported Codex contracts

- Depth-2 stage dispatch: registered but app-server initialization failed with read-only filesystem; `manual-main-session` fallback used.
- Qualified `apply_patch` target detection: unavailable for some writes; explicit preflight plus shell `apply_patch` fallback used.

## Handoff

Main orchestrator owns final diff review, commit/push, runtime projection restoration, merge, and worktree cleanup.
