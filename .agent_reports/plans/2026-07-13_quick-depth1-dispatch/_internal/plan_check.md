# plan-check-lite

## Requirements Coverage

Pass with notes.

- Direct depth 0 inline is covered.
- Quick depth 1 one-shot worker is covered.
- Quick depth 2 forbidden is covered.
- Standard+ depth1-to-depth2 topology is explicitly preserved.
- Mutation quick isolated worktree is covered.
- Codex fallback order and Fleet degradation note are covered.
- Fleet `quick/exec` one-stage rendering and quick depth2 violation are covered.
- Core-first, capabilities, compatibility sources, generated projections, adapter bootstraps/prompts, Fleet, guards/tests, and sync generation are all included.
- Drill is explicitly excluded.

## Over/Under Scope

Pass.

This plan does not ask `code-execute` to redesign dispatch topology beyond PRD v6. It does require broad surface edits because PRD v6 is cross-cutting. It separates current uncommitted core changes from remaining drift so the executor can avoid overwriting concurrent work.

## Executable Verification

Pass.

The plan names deterministic checks for portable guards, Fleet unit tests, projection sync checks, boundary/mirror checks, doctor/runtime checks, quick depth1/depth2 dispatch probes, and `git diff --check`. Concrete command evidence belongs in the later `code-test` stage under `test_logs/`.

## Missed Spec-Significant Risk

Residual risk remains.

- `route autopilot-code` did not accept the PRD read marker in this Codex headless environment despite actual PRD reads and `preflight.sh read` attempts under writable `AGENT_HOME=$PWD`. If it persists during source edits, report as an unsupported Codex marker/runtime quirk rather than silently ignoring the gate.
- Some generated projections may be source-derived from Claude mirror files. Executor must use the repo's established sync path rather than manually editing only Codex/OpenCode projections.
- Fleet mirror parity can drift because `tools/fleet` and `adapters/claude/tools/fleet` both exist.

Plan-check verdict: PASS for execution handoff.
