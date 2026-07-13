# Pipeline Summary

## Changed Files

- Spec/artifacts: `.agent_reports/spec/agent-fleet-dashboard/prd.md`, `.agent_reports/spec/agent-fleet-dashboard/_internal/versions/v3/prd.md`, `.agent_reports/plans/2026-07-13_runtime-currentness/`.
- Fleet: `tools/fleet/**` and mirrored `adapters/claude/tools/fleet/**`.
- Dispatch policy: `core/OPERATIONS.md`, `skills/autopilot-code/references/dev-pipeline.md`, `adapters/claude/skills/autopilot-code/references/dev-pipeline.md`, `utilities/usage-check.sh`, `utilities/usage-check.test.sh`.
- Runtime-watch loop/projection: `loops/runtime-watch.*`, `loops/README.md`, `loops/oncall.md`, `adapters/claude/loops/**`, Codex/OpenCode preflight and docs, `INSTALL_LAYOUT.md`, `README.md`, `manifest.json`, `tools/build-manifest.py`, `tools/check-adaptation-boundary.sh`.

## Verification

See `test_logs/verification.md` for command evidence. Final verification passed for fleet tests, usage-check tests, shell syntax, runtime-watch probe, manifest/native sync checks, adaptation boundary, Codex doctor, and `git diff --check`.

## Unsupported / Fallback Contracts

- Independent QA delegation was not run; inline fallback is recorded under `_internal/metrics.md`.
- Runtime-watch does not auto-edit policy. It fingerprints normalized visible source text, ignores probe timestamps for change detection, and reports unavailable official fetches or local projection drift instead of hiding them.
- Installed `$CODEX_HOME` runtime projection is not rewired by this branch; loop probe reports the current state for follow-up.
- The headless worker could not write the parent worktree gitdir; the main orchestrator performed final review, commit, and push.
