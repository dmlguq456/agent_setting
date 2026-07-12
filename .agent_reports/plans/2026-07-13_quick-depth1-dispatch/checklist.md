# quick-depth1-dispatch checklist

## Code-plan

- [x] Read Codex adapter bootstrap.
- [x] Ran `status`, `prompt-signal`, `mode`, `mode-info dev/refactor`, `qa-policy standard code`.
- [x] Read `autopilot-code` and `code-plan` Codex skills and portable capability contracts.
- [x] Read PRD v6 and current core/capability/adapter/Fleet/test surfaces.
- [x] Emitted spec-significance verdict in `plan.md`.
- [x] Selected stage graph in `plan.md`.
- [x] Wrote plan-only handoff artifacts.

## Execute Stage

- [x] Re-read current dirty `core/*.md` diffs before editing.
- [x] Core SoT first: finish v6 quick depth1 wording in core docs.
- [x] Update portable capability contracts, especially `capabilities/autopilot-code.md` and `capabilities/code-plan.md`.
- [x] Update adapter bootstraps and dispatch prompts for Codex/OpenCode/Claude mirror.
- [x] Preserve validator behavior: quick depth1 accepted, quick depth2 rejected.
- [x] Add/adjust Fleet quick depth1 `quick/exec` rendering and quick depth2 violation tests.
- [x] Run sync-skills / native projection generation after source edits.
- [x] Keep source mutation in the correct isolated worktree path.

## Test Stage

- [x] Run portable guards.
- [x] Run Fleet tests.
- [x] Run projection checks for Codex/OpenCode.
- [x] Run adaptation boundary/mirror checks.
- [ ] Run Codex/OpenCode doctor/runtime checks as available.
- [x] Run `git diff --check`.
- [x] Record evidence under `test_logs/`.

## Report Stage

- [ ] Write/update `pipeline_summary.md`.
- [ ] Include changed files, commands/results, artifact paths, and unsupported runtime contracts.
- [ ] Leave merge and worktree cleanup to the main orchestrator.
